from typing import TYPE_CHECKING, List, Optional, cast

from django.db import IntegrityError
from django.db.models import QuerySet

from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.pages.constants import (
    ILLEGAL_PATH_SAMPLE_CHARACTER,
    PAGE_PATH_PARAM_PREFIX,
    PATH_PARAM_REGEX,
)
from baserow.contrib.builder.pages.exceptions import (
    DuplicatePathParamsInPath,
    PageDoesNotExist,
    PageNameNotUnique,
    PageNotInBuilder,
    PagePathNotUnique,
    PathParamNotDefined,
    PathParamNotInPath,
)
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.pages.types import PagePathParams
from baserow.core.exceptions import IdDoesNotExist
from baserow.core.registries import application_type_registry
from baserow.core.utils import ChildProgressBuilder, find_unused_name

if TYPE_CHECKING:
    from baserow.contrib.builder.application_types import BuilderApplicationType


class PageHandler:
    def get_page(self, page_id: int, base_queryset: QuerySet = None) -> Page:
        """
        Gets a page by ID

        :param page_id: The ID of the page
        :param base_queryset: Can be provided to already filter or apply performance
            improvements to the queryset when it's being executed
        :raises PageDoesNotExist: If the page doesn't exist
        :return: The model instance of the Page
        """

        if base_queryset is None:
            base_queryset = Page.objects

        try:
            return base_queryset.select_related("builder", "builder__workspace").get(
                id=page_id
            )
        except Page.DoesNotExist:
            raise PageDoesNotExist()

    def create_page(
        self,
        builder: Builder,
        name: str,
        path: str,
        path_params: PagePathParams = None,
    ) -> Page:
        """
        Creates a new page

        :param builder: The builder the page belongs to
        :param name: The name of the page
        :param path: The path of the page
        :param path_params: The params of the path provided
        :return: The newly created page instance
        """

        last_order = Page.get_last_order(builder)
        path_params = path_params or []

        self.is_page_path_valid(path, path_params, raises=True)
        self.is_page_path_unique(builder, path, raises=True)

        try:
            page = Page.objects.create(
                builder=builder,
                name=name,
                order=last_order,
                path=path,
                path_params=path_params,
            )
        except IntegrityError as e:
            if "unique constraint" in e.args[0] and "name" in e.args[0]:
                raise PageNameNotUnique(name=name, builder_id=builder.id)
            if "unique constraint" in e.args[0] and "path" in e.args[0]:
                raise PagePathNotUnique(path=path, builder_id=builder.id)
            raise e

        return page

    def delete_page(self, page: Page):
        """
        Deletes the page provided

        :param page: The page that must be deleted
        """

        page.delete()

    def update_page(self, page: Page, **kwargs) -> Page:
        """
        Updates fields of a page

        :param page: The page that should be updated
        :param kwargs: The fields that should be updated with their corresponding value
        :return: The updated page
        """

        if "path" in kwargs or "path_params" in kwargs:
            path = kwargs.get("path", page.path)
            path_params = kwargs.get("path_params", page.path_params)

            self.is_page_path_valid(path, path_params, raises=True)
            self.is_page_path_unique(
                page.builder,
                path,
                base_queryset=Page.objects.exclude(
                    id=page.id
                ),  # We don't want to conflict with the current page
                raises=True,
            )

        for key, value in kwargs.items():
            setattr(page, key, value)

        try:
            page.save()
        except IntegrityError as e:
            if "unique constraint" in e.args[0] and "name" in e.args[0]:
                raise PageNameNotUnique(name=page.name, builder_id=page.builder_id)
            if "unique constraint" in e.args[0] and "path" in e.args[0]:
                raise PagePathNotUnique(path=page.path, builder_id=page.builder_id)
            raise e

        return page

    def order_pages(
        self, builder: Builder, order: List[int], base_qs=None
    ) -> List[int]:
        """
        Assigns a new order to the pages in a builder application.
        You can provide a base_qs for pre-filter the pages affected by this change.

        :param builder: The builder that the pages belong to
        :param order: The new order of the pages
        :param base_qs: A QS that can have filters already applied
        :raises PageNotInBuilder: If the page is not part of the provided builder
        :return: The new order of the pages
        """

        if base_qs is None:
            base_qs = Page.objects.filter(builder=builder)

        try:
            full_order = Page.order_objects(base_qs, order)
        except IdDoesNotExist as error:
            raise PageNotInBuilder(error.not_existing_id)

        return full_order

    def duplicate_page(
        self, page: Page, progress_builder: Optional[ChildProgressBuilder] = None
    ):
        """
        Duplicates an existing page instance

        :param page: The page that is being duplicated
        :param progress_builder: A progress object that can be used to report progress
        :raises ValueError: When the provided page is not an instance of Page.
        :return: The duplicated page
        """

        start_progress, export_progress, import_progress = 10, 30, 60
        progress = ChildProgressBuilder.build(progress_builder, child_total=100)
        progress.increment(by=start_progress)

        builder = page.builder
        builder_application_type = cast(
            "BuilderApplicationType", application_type_registry.get_by_model(builder)
        )

        [exported_page] = builder_application_type.export_pages_serialized([page])

        # Set a unique name for the page to import back as a new one.
        exported_page["name"] = self.find_unused_page_name(builder, page.name)
        exported_page["path"] = self.find_unused_page_path(builder, page.path)
        exported_page["order"] = Page.get_last_order(builder)

        progress.increment(by=export_progress)

        [new_page_clone] = builder_application_type.import_pages_serialized(
            builder,
            [exported_page],
            progress_builder=progress.create_child_builder(
                represents_progress=import_progress
            ),
            id_mapping={},
        )

        return new_page_clone

    def find_unused_page_name(self, builder: Builder, proposed_name: str) -> str:
        """
        Finds an unused name for a page in a builder.

        :param builder: The builder that the page belongs to.
        :param proposed_name: The name that is proposed to be used.
        :return: A unique name to use.
        """

        existing_pages_names = list(builder.page_set.values_list("name", flat=True))
        return find_unused_name([proposed_name], existing_pages_names, max_length=255)

    def find_unused_page_path(self, builder: Builder, proposed_path: str) -> str:
        """
        Find an unused path for a page in a builder.

        :param builder: The builder that the page belongs to.
        :param proposed_path: The path that is proposed to be used.
        :return: A unique path to use
        """

        existing_paths = list(builder.page_set.values_list("path", flat=True))
        return find_unused_name(
            [proposed_path], existing_paths, max_length=255, suffix="{0}"
        )

    def is_page_path_valid(
        self, path: str, path_params: PagePathParams, raises: bool = False
    ) -> bool:
        """
        Checks if a path object is constructed correctly. If there is a mismatch
        between the path itself and the path params for example, it becomes an invalid
        path.

        :param path: The path in question
        :param path_params: The param definitions of the path provided
        :param raises: If true, raises exceptions instead of returning a boolean
        :raises PathParamNotInPath: If the path param is not in the path
        :raises PathParamNotDefined: If a param in the path was not defined as a path
            param in the path_params provided
        :return: If the path is valid
        """

        path_param_names = [p["name"] for p in path_params]

        # Make sure all path params are also in the path
        for path_param_name in path_param_names:
            if f"{PAGE_PATH_PARAM_PREFIX}{path_param_name}" not in path:
                if raises:
                    raise PathParamNotInPath(path, path_param_name)
                return False

        path_params_in_path = PATH_PARAM_REGEX.findall(path)
        unique_path_params_in_path = set(path_params_in_path)

        if len(unique_path_params_in_path) != len(path_params_in_path):
            duplicate_path_param_names = [
                name
                for name in path_param_names
                if name not in unique_path_params_in_path
            ]
            if raises:
                raise DuplicatePathParamsInPath(path, duplicate_path_param_names)
            return False

        for path_param_in_path in path_params_in_path:
            param_name = path_param_in_path[1:]

            if param_name not in path_param_names:
                if raises:
                    raise PathParamNotDefined(path, param_name, path_param_names)
                return False

        return True

    def is_page_path_unique(
        self,
        builder: Builder,
        path: str,
        base_queryset: QuerySet = None,
        raises: bool = False,
    ) -> bool:
        """
        Checks if a page path is unique.

        :param builder: The builder that the page belongs to
        :param path: The path it is trying to set
        :param raises: If true will raise an exception when the path isn't unique
        :return: If the path is unique
        """

        queryset = Page.objects if base_queryset is None else base_queryset

        existing_paths = queryset.filter(builder=builder).values_list("path", flat=True)

        path_generalised = self.generalise_path(path)
        for existing_path in existing_paths:
            if self.generalise_path(existing_path) == path_generalised:
                if raises:
                    raise PagePathNotUnique(path=path, builder_id=builder.id)
                return False

        return True

    def generalise_path(self, path: str) -> str:
        """
        Returns a generalised version of a path. This can be useful if we are trying to
        understand if 2 paths are equivalent even if their path params have different
        names.

        For 2 paths to be equivalent they need to have the same static parts of the path
        and the same amount and position of path parameters.

        Equivalent:
        /product/:id, /product/:new
        /product/:id/hello/:new, /product/:new/hello/:id

        Not equivalent:
        /product/:id, /product/:id/:new
        /product/:id/hello/:new, /product/:id/:new/hello

        By replacing all the path parameters in the path with an illegal path character
        we can make sure that we can match 2 paths and, they will be the same string if
        they are indeed a duplicate given the above rules.

        :param path: The path that is being generalised
        :return: The generalised path
        """

        return PATH_PARAM_REGEX.sub(ILLEGAL_PATH_SAMPLE_CHARACTER, path)

from typing import List, Optional

from django.db.models import QuerySet

from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.pages.exceptions import PageDoesNotExist, PageNotInBuilder
from baserow.contrib.builder.pages.models import Page
from baserow.core.exceptions import IdDoesNotExist
from baserow.core.registries import application_type_registry
from baserow.core.utils import ChildProgressBuilder, find_unused_name


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
            return base_queryset.get(id=page_id)
        except Page.DoesNotExist:
            raise PageDoesNotExist()

    def create_page(self, builder: Builder, name: str) -> Page:
        """
        Creates a new page

        :param builder: The builder the page belongs to
        :param name: The name of the page
        :return: The newly created page instance
        """

        last_order = Page.get_last_order(builder)
        page = Page.objects.create(builder=builder, name=name, order=last_order)

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
        :param values: The fields that should be updated with their corresponding value
        :return: The updated page
        """

        for key, value in kwargs.items():
            setattr(page, key, value)

        page.save()

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
        builder_application_type = application_type_registry.get_by_model(builder)

        [exported_page] = builder_application_type.export_pages_serialized([page])

        # Set a unique name for the page to import back as a new one.
        exported_page["name"] = self.find_unused_page_name(builder, page.name)
        exported_page["order"] = Page.get_last_order(builder)

        progress.increment(by=export_progress)

        [new_page_clone] = builder_application_type.import_pages_serialized(
            builder,
            [exported_page],
            progress_builder=progress.create_child_builder(
                represents_progress=import_progress
            ),
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

from typing import Any, Dict, List, Optional
from zipfile import ZipFile

from django.contrib.auth.models import AbstractUser
from django.core.files.storage import Storage
from django.db import transaction
from django.db.transaction import Atomic
from django.urls import include, path
from django.utils import translation
from django.utils.translation import gettext as _

from baserow.contrib.builder.api.serializers import BuilderSerializer
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.pages.service import PageService
from baserow.contrib.builder.types import BuilderDict, PageDict
from baserow.contrib.database.constants import IMPORT_SERIALIZED_IMPORTING
from baserow.core.db import specific_iterator
from baserow.core.models import Application, Workspace
from baserow.core.registries import ApplicationType, ImportExportConfig
from baserow.core.utils import ChildProgressBuilder


class BuilderApplicationType(ApplicationType):
    type = "builder"
    model_class = Builder
    instance_serializer_class = BuilderSerializer
    supports_integrations = True

    def get_api_urls(self):
        from .api import urls as api_urls

        return [
            path("builder/", include(api_urls, namespace=self.type)),
        ]

    def export_safe_transaction_context(self, application: Application) -> Atomic:
        return transaction.atomic()

    def init_application(self, user: AbstractUser, application: Application) -> None:
        with translation.override(user.profile.language):
            first_page_name = _("Homepage")

        PageService().create_page(user, application.specific, first_page_name, path="/")

    def export_pages_serialized(
        self,
        pages: List[Page],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> List[PageDict]:
        """
        Exports all the pages given to a format that can be imported again to baserow
        via `import_pages_serialized`.

        :param pages: The pages that are supposed to be exported
        :param files_zip: A zip file buffer where the files related to the pages
            must be copied into.
        :type files_zip: ZipFile
        :param storage: The storage where the files can be loaded from.
        :type storage: Storage or None
        :return: The list of serialized pages.
        """

        serialized_pages: List[PageDict] = []
        for page in pages:
            # Get serialized version of all elements of the current page
            serialized_elements = []
            for element in specific_iterator(page.element_set.all()):
                element_type = element_type_registry.get_by_model(element)
                serialized_elements.append(element_type.export_serialized(element))

            serialized_pages.append(
                PageDict(
                    id=page.id,
                    name=page.name,
                    order=page.order,
                    path=page.path,
                    path_params=page.path_params,
                    elements=serialized_elements,
                )
            )
        return serialized_pages

    def export_serialized(
        self,
        builder: Builder,
        import_export_config: ImportExportConfig,
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> BuilderDict:
        """
        Exports the builder application type to a serialized format that can later
        be imported via the `import_serialized`.
        """

        pages = builder.page_set.all().prefetch_related(
            "element_set",
        )

        serialized_pages = self.export_pages_serialized(pages, files_zip, storage)

        serialized = super().export_serialized(
            builder, import_export_config, files_zip, storage
        )

        return BuilderDict(pages=serialized_pages, **serialized)

    def _ops_count_for_import_pages_serialized(
        self,
        serialized_pages: List[Dict[str, Any]],
    ) -> int:
        return (
            # Creating each page
            len(serialized_pages)
            + sum(
                [
                    # Inserting every field
                    len(page["elements"])
                    for page in serialized_pages
                ]
            )
        )

    def import_pages_serialized(
        self,
        builder: Builder,
        serialized_pages: List[Dict[str, Any]],
        id_mapping: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> List[Page]:
        """
        Import pages to builder. This method has to be compatible with the output
        of `export_pages_serialized`.

        :param builder: The builder the pages where exported from.
        :param serialized_pages: The pages that are supposed to be imported.
        :param progress_builder: A progress builder that allows for publishing progress.
        :param files_zip: An optional zip file for the related files.
        :param storage: The storage instance.
        :return: The created page instances.
        """

        child_total = self._ops_count_for_import_pages_serialized(serialized_pages)
        progress = ChildProgressBuilder.build(progress_builder, child_total=child_total)

        if "import_workspace_id" not in id_mapping and builder.workspace is not None:
            id_mapping["import_workspace_id"] = builder.workspace.id

        if "builder_pages" not in id_mapping:
            id_mapping["builder_pages"] = {}

        if "workspace_id" not in id_mapping and builder.workspace is not None:
            id_mapping["workspace_id"] = builder.workspace.id

        imported_pages: List[Page] = []

        # First, we want to create all the page instances because it could be that
        # element depends on the existence of a page.
        for serialized_page in serialized_pages:
            page_instance = Page.objects.create(
                builder=builder,
                name=serialized_page["name"],
                order=serialized_page["order"],
                path=serialized_page["path"],
                path_params=serialized_page["path_params"],
            )
            id_mapping["builder_pages"][serialized_page["id"]] = page_instance.id
            serialized_page["_object"] = page_instance
            serialized_page["_element_objects"] = []
            imported_pages.append(page_instance)
            progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        # Then we create all the element instances.
        for serialized_page in serialized_pages:
            for serialized_element in serialized_page["elements"]:
                element_type = element_type_registry.get(serialized_element["type"])
                element_instance = element_type.import_serialized(
                    serialized_page["_object"], serialized_element, id_mapping
                )

                serialized_page["_element_objects"].append(element_instance)

                progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        return imported_pages

    def import_serialized(
        self,
        workspace: Workspace,
        serialized_values: Dict[str, Any],
        import_export_config: ImportExportConfig,
        id_mapping: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> Application:
        """
        Imports a builder application exported by the `export_serialized` method.
        """

        serialized_pages = serialized_values.pop("pages")
        builder_progress, page_progress = 5, 95
        progress = ChildProgressBuilder.build(
            progress_builder, child_total=builder_progress + page_progress
        )

        application = super().import_serialized(
            workspace,
            serialized_values,
            import_export_config,
            id_mapping,
            files_zip,
            storage,
            progress.create_child_builder(represents_progress=builder_progress),
        )

        builder = application.specific

        if not serialized_pages:
            progress.increment(state=IMPORT_SERIALIZED_IMPORTING, by=page_progress)
        else:
            self.import_pages_serialized(
                builder,
                serialized_pages,
                id_mapping,
                files_zip,
                storage,
                progress.create_child_builder(represents_progress=page_progress),
            )

        return builder

    def enhance_queryset(self, queryset):
        return queryset.prefetch_related("page_set")

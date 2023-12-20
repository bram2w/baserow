from typing import Any, Dict, Iterable, Optional, Union
from zipfile import ZipFile

from django.core.files.storage import Storage
from django.db.models import QuerySet

from baserow.contrib.builder.data_sources.builder_dispatch_context import (
    BuilderDispatchContext,
)
from baserow.contrib.builder.data_sources.exceptions import (
    DataSourceDoesNotExist,
    DataSourceImproperlyConfigured,
)
from baserow.contrib.builder.data_sources.models import DataSource
from baserow.contrib.builder.formula_importer import import_formula
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.types import DataSourceDict
from baserow.core.integrations.models import Integration
from baserow.core.integrations.registries import integration_type_registry
from baserow.core.services.handler import ServiceHandler
from baserow.core.services.models import Service
from baserow.core.services.registries import ServiceType
from baserow.core.utils import find_unused_name

from .types import DataSourceForUpdate


class DataSourceHandler:
    def __init__(self):
        self.service_handler = ServiceHandler()

    def get_data_source(
        self, data_source_id: int, base_queryset: Optional[QuerySet] = None
    ) -> DataSource:
        """
        Returns a data_source instance from the database.

        :param data_source_id: The ID of the data_source.
        :param base_queryset: The base queryset to use to build the query.
        :raises DataSourceDoesNotExist: If the data_source can't be found.
        :return: The data_source instance.
        """

        queryset = (
            base_queryset if base_queryset is not None else DataSource.objects.all()
        )

        try:
            data_source = queryset.select_related(
                "page", "page__builder", "page__builder__workspace", "service"
            ).get(id=data_source_id)
        except DataSource.DoesNotExist:
            raise DataSourceDoesNotExist()

        return data_source

    def get_data_source_for_update(
        self, data_source_id: int, base_queryset=None
    ) -> DataSourceForUpdate:
        """
        Returns a data_source instance from the database that can be safely updated.

        :param data_source_id: The ID of the data_source.
        :param base_queryset: The base queryset to use to build the query.
        :raises DataSourceDoesNotExist: If the data_source can't be found.
        :return: The data_source instance.
        """

        queryset = (
            base_queryset if base_queryset is not None else DataSource.objects.all()
        )

        queryset = queryset.select_for_update(of=("self",))

        return self.get_data_source(
            data_source_id,
            base_queryset=queryset,
        )

    def get_data_sources(
        self,
        page: Page,
        base_queryset: Optional[QuerySet] = None,
        specific: bool = True,
    ) -> Union[QuerySet[DataSource], Iterable[DataSource]]:
        """
        Gets all the specific data_sources of a given page.

        :param page: The page that holds the data_sources.
        :param base_queryset: The base queryset to use to build the query.
        :param specific: If True, return the specific version of the service related
          to the integration
        :return: The data_sources of that page.
        """

        data_source_queryset = (
            base_queryset if base_queryset is not None else DataSource.objects.all()
        )

        data_source_queryset = data_source_queryset.filter(page=page).select_related(
            "service",
            "page",
            "page__builder",
            "page__builder__workspace",
            "service",
            "service__integration",
            "service__integration__application",
        )

        if specific:
            data_source_queryset = data_source_queryset.select_related(
                "service__content_type"
            )
            data_sources = list(data_source_queryset.all())

            # Get all service ids to get them from DB in one query
            service_ids = [
                data_source.service_id
                for data_source in data_sources
                if data_source.service_id is not None
            ]

            specific_services_map = {
                s.id: s
                for s in ServiceHandler().get_services(
                    base_queryset=Service.objects.filter(id__in=service_ids)
                )
            }

            # Distribute specific services to their data_source
            for data_source in data_sources:
                if data_source.service_id:
                    data_source.service = specific_services_map[data_source.service_id]

            return data_sources
        else:
            return data_source_queryset.all()

    def find_unused_data_source_name(self, page: Page, proposed_name: str) -> str:
        """
        Finds an unused name for a page in a builder.

        :param builder: The builder that the page belongs to.
        :param proposed_name: The name that is proposed to be used.
        :return: A unique name to use.
        """

        existing_pages_names = list(
            DataSource.objects.filter(page__builder=page.builder).values_list(
                "name", flat=True
            )
        )
        return find_unused_name([proposed_name], existing_pages_names, max_length=255)

    def create_data_source(
        self,
        page: Page,
        name: str,
        service_type: Optional[ServiceType] = None,
        before: Optional[DataSource] = None,
        **kwargs,
    ) -> DataSource:
        """
        Creates a new data_source for a page.

        :param page: The page the data_source exists in.
        :param name: The human name of the data_source.
        :param service_type: The type of the service related to the data_source.
        :param before: If set, the new data_source is inserted before this data_source.
        :param kwargs: Additional attributes of the related service.
        :raises CannotCalculateIntermediateOrder: If it's not possible to find an
            intermediate order. The full order of the data_source of the page must be
            recalculated in this case before calling this method again.
        :return: The created data_source.
        """

        if before:
            order = DataSource.get_unique_order_before_data_source(before)
        else:
            order = DataSource.get_last_order(page)

        if service_type:
            service = self.service_handler.create_service(
                service_type=service_type, **kwargs
            )
        else:
            service = None

        data_source = DataSource.objects.create(
            page=page, order=order, name=name, service=service
        )
        data_source.save()

        return data_source

    def update_data_source(
        self,
        data_source: DataSourceForUpdate,
        service_type: Optional[ServiceType] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> DataSource:
        """
        Updates a data_source and the related service with values.

        :param data_source: The data_source that should be updated.
        :param name: A new name for the data_source.
        :param values: The values that should be set on the data_source.
        :return: The updated data_source.
        """

        if "new_service_type" in kwargs:
            new_service_type = kwargs.pop("new_service_type")

            integration = None
            integration_type = None
            if data_source.service:
                integration = data_source.service.integration
                ServiceHandler().delete_service(service_type, data_source.service)
                data_source.service = None

            if integration:
                integration_type = integration_type_registry.get_by_model(
                    integration.specific
                ).type

            if new_service_type:
                # Check if the new service type can reuse the previous integration
                if new_service_type.integration_type != integration_type:
                    integration = None

                service = self.service_handler.create_service(
                    service_type=new_service_type,
                    integration=integration,
                    **kwargs,
                )
                data_source.service = service

        if data_source.service and kwargs:
            service_to_update = self.service_handler.get_service_for_update(
                data_source.service.id
            )
            self.service_handler.update_service(
                service_type, service_to_update, **kwargs
            )
            data_source.service = service_to_update

        if name is not None:
            data_source.name = name

        data_source.save()

        return data_source

    def delete_data_source(self, data_source: DataSource):
        """
        Deletes an data_source.

        :param data_source: The to-be-deleted data_source.
        """

        data_source.delete()

    def dispatch_data_sources(
        self, data_sources, dispatch_context: BuilderDispatchContext
    ):
        """
        Dispatch the service related to the data_sources.

        :param data_sources: The data sources to be dispatched.
        :param dispatch_context: The context used for the dispatch.
        :return: The result of dispatching the data source mapped by data source ID.
            If an Exception occurred during the dispatch the exception is return as
            result for this data source.
        """

        data_sources_dispatch = {}
        for data_source in data_sources:
            # Add the initial call to the call stack
            dispatch_context.add_call(data_source.id)
            try:
                data_sources_dispatch[data_source.id] = self.dispatch_data_source(
                    data_source, dispatch_context
                )
            except Exception as e:
                data_sources_dispatch[data_source.id] = e
            # Reset the stack as we are starting a new dispatch
            dispatch_context.reset_call_stack()

        return data_sources_dispatch

    def dispatch_data_source(
        self, data_source: DataSource, dispatch_context: BuilderDispatchContext
    ) -> Any:
        """
        Dispatch the service related to the data_source.

        :param data_source: The data source to be dispatched.
        :param dispatch_context: The context used for the dispatch.
        :raises DataSourceImproperlyConfigured: If the data source is
          not properly configured.
        :return: The result of dispatching the data source.
        """

        if not data_source.service_id:
            raise DataSourceImproperlyConfigured("The service type is missing.")

        if data_source.id not in dispatch_context.cache.setdefault(
            "data_source_contents", {}
        ):
            service_dispatch = self.service_handler.dispatch_service(
                data_source.service.specific, dispatch_context
            )
            # Cache the dispatch in the formula cache if we have formulas that need
            # it later
            dispatch_context.cache["data_source_contents"][
                data_source.id
            ] = service_dispatch

        return dispatch_context.cache["data_source_contents"][data_source.id]

    def move_data_source(
        self, data_source: DataSourceForUpdate, before: Optional[DataSource] = None
    ) -> DataSource:
        """
        Moves the given data_source before the specified `before` data_source in the
        same page.

        :param data_source: The data_source to move.
        :param before: The data_source before which to move the `data_source`. If
            before is not specified, the data_source is moved at the end of the list.
        :raises CannotCalculateIntermediateOrder: If it's not possible to find an
            intermediate order. The full order of the data_source of the page must be
            recalculated in this case before calling this method again.
        :return: The moved data_source.
        """

        if before:
            data_source.order = DataSource.get_unique_order_before_data_source(before)
        else:
            data_source.order = DataSource.get_last_order(data_source.page)

        data_source.save()

        return data_source

    def recalculate_full_orders(
        self,
        page: Page,
    ):
        """
        Recalculates the order to whole numbers of all data_sources of the given page.
        """

        DataSource.recalculate_full_orders(
            queryset=DataSource.objects.filter(page=page)
        )

    def export_data_source(
        self,
        data_source: DataSource,
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> DataSourceDict:
        """
        Serializes the given data source.

        :param data_source: The data source instance to serialize.
        :param files_zip: A zip file to store files in necessary.
        :param storage: Storage to use.
        :return: The serialized version.
        """

        serialized_service = None

        if data_source.service:
            serialized_service = ServiceHandler().export_service(data_source.service)

        return DataSourceDict(
            id=data_source.id,
            name=data_source.name,
            order=str(data_source.order),
            service=serialized_service,
        )

    def import_data_source(
        self,
        page,
        serialized_data_source: DataSourceDict,
        id_mapping: Dict[str, Dict[int, int]],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ):
        """
        Creates an instance using the serialized version previously exported with
        `.export_data_source'.

        :param page: The page instance the new data source should belong to.
        :param serialized_data_source: The serialized version of the data source.
        :param id_mapping: A map of old->new id per data type
            when we have foreign keys that need to be migrated.
        :param files_zip: Contains files to import if any.
        :param storage: Storage to get the files from.
        :return: the new data source instance.
        """

        if "builder_data_sources" not in id_mapping:
            id_mapping["builder_data_sources"] = {}

        # First we get the service if any
        service = None
        serialized_service = serialized_data_source.get("service", None)
        if serialized_service:
            # Get the integration if any
            integration = None
            integration_id = serialized_service.pop("integration_id", None)
            if integration_id:
                integration_id = id_mapping["integrations"].get(
                    integration_id, integration_id
                )
                integration = Integration.objects.get(id=integration_id)

            service = ServiceHandler().import_service(
                integration,
                serialized_service,
                id_mapping,
                files_zip=files_zip,
                storage=storage,
                import_formula=import_formula,
            )

        # Then create the data source with the service
        data_source = DataSource.objects.create(
            page=page,
            service=service,
            order=serialized_data_source["order"],
            name=serialized_data_source["name"],
        )

        id_mapping["builder_data_sources"][
            serialized_data_source["id"]
        ] = data_source.id

        return data_source

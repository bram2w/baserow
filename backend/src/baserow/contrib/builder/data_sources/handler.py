from typing import Iterable, Optional, Union

from django.db.models import QuerySet

from baserow.contrib.builder.data_sources.exceptions import DataSourceDoesNotExist
from baserow.contrib.builder.data_sources.models import DataSource
from baserow.contrib.builder.pages.models import Page
from baserow.core.db import specific_iterator
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
        :return: The data_sources of that page.
        """

        data_source_queryset = (
            (base_queryset if base_queryset is not None else DataSource.objects.all())
            .filter(page=page)
            .select_related("service")
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

            # Use specific iterator to get specific instance of services
            specific_services_map = {
                s.id: s
                for s in specific_iterator(Service.objects.filter(id__in=service_ids))
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

            if data_source.service:
                ServiceHandler().delete_service(data_source.service)
                data_source.service = None

            if new_service_type:
                service = self.service_handler.create_service(
                    service_type=new_service_type, **kwargs
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

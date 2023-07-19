from typing import Iterable, Optional, Union, cast

from django.db.models import QuerySet

from baserow.contrib.builder.pages.models import Page
from baserow.core.db import specific_iterator
from baserow.core.integrations.models import Integration
from baserow.core.services.exceptions import ServiceDoesNotExist
from baserow.core.services.models import Service
from baserow.core.services.registries import ServiceType
from baserow.core.utils import extract_allowed

from .types import ServiceForUpdate


class ServiceHandler:
    def get_service(
        self, service_id: int, base_queryset: QuerySet[Service] = None
    ) -> Service:
        """
        Returns an service instance from the database.

        :param service_id: The ID of the service.
        :param base_queryset: The base queryset to use to build the query.
        :raises ServiceDoesNotExist: If the service can't be found.
        :return: The service instance.
        """

        queryset = base_queryset if base_queryset is not None else Service.objects.all()

        try:
            service = (
                queryset.select_related(
                    "integration",
                    "integration__application",
                    "integration__application__workspace",
                )
                .get(id=service_id)
                .specific
            )
        except Service.DoesNotExist:
            raise ServiceDoesNotExist()

        return service

    def get_service_for_update(
        self, service_id: int, base_queryset: QuerySet[Service] = None
    ) -> ServiceForUpdate:
        """
        Returns an service instance from the database that can be safely updated.

        :param service_id: The ID of the service.
        :param base_queryset: The base queryset to use to build the query.
        :raises ServiceDoesNotExist: If the service can't be found.
        :return: The service instance.
        """

        queryset = base_queryset if base_queryset is not None else Service.objects.all()

        queryset = queryset.select_for_update(of=("self",))

        return self.get_service(
            service_id,
            base_queryset=queryset,
        )

    def get_services(
        self,
        integration: Integration,
        base_queryset: Optional[QuerySet] = None,
        specific: bool = True,
    ) -> Union[QuerySet[Page], Iterable[Page]]:
        """
        Gets all the specific services of a given integration.

        :param integration: The integration that holds the services.
        :param base_queryset: The base queryset to use to build the query.
        :param specific: Whether to return the generic services or the specific
            instances.
        :return: The services of that page.
        """

        queryset = base_queryset if base_queryset is not None else Service.objects.all()

        queryset = queryset.filter(integration=integration)

        if specific:
            queryset = queryset.select_related("content_type")
            return specific_iterator(queryset)
        else:
            return queryset

    def create_service(self, service_type: ServiceType, **kwargs) -> Service:
        """
        Creates a new service.

        :param service_type: The type of the service.
        :param kwargs: Additional attributes of the service.
        :return: The created service.
        """

        shared_allowed_fields = ["type", "integration"]
        allowed_values = extract_allowed(
            kwargs, shared_allowed_fields + service_type.allowed_fields
        )

        model_class = cast(Service, service_type.model_class)

        service = model_class(**allowed_values)
        service.save()

        return service

    def delete_service(self, service: Service):
        """
        Deletes an service.

        :param service: The to-be-deleted service.
        """

        service.delete()

    def update_service(
        self, service_type: ServiceType, service: ServiceForUpdate, **kwargs
    ) -> Service:
        """
        Updates and service with values. Will also check if the values are allowed
        to be set on the service first.

        :param service: The service that should be updated.
        :param values: The values that should be set on the service.
        :return: The updated service.
        """

        shared_allowed_fields = ["integration"]
        allowed_updates = extract_allowed(
            kwargs, shared_allowed_fields + service_type.allowed_fields
        )

        for key, value in allowed_updates.items():
            setattr(service, key, value)

        service.save()

        return service

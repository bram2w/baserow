from typing import List

from django.db.models import QuerySet

from baserow.contrib.builder.domains.exceptions import (
    DomainDoesNotExist,
    DomainNotInBuilder,
)
from baserow.contrib.builder.domains.models import Domain
from baserow.contrib.builder.models import Builder
from baserow.core.exceptions import IdDoesNotExist


class DomainHandler:
    def get_domain(self, domain_id: int, base_queryset: QuerySet = None) -> Domain:
        """
        Gets a domain by ID

        :param domain_id: The ID of the domain
        :param base_queryset: Can be provided to already filter or apply performance
            improvements to the queryset when it's being executed
        :raises DomainDoesNotExist: If the domain doesn't exist
        :return: The model instance of the domain
        """

        if base_queryset is None:
            base_queryset = Domain.objects

        try:
            return base_queryset.get(id=domain_id)
        except Domain.DoesNotExist:
            raise DomainDoesNotExist()

    def get_domains(
        self, builder: Builder, base_queryset: QuerySet = None
    ) -> QuerySet[Domain]:
        """
        Gets all the domains of a builder.

        :param builder: The builder we are trying to get all domains for
        :param base_queryset: Can be provided to already filter or apply performance
            improvements to the queryset when it's being executed
        :return: A queryset with all the domains
        """

        if base_queryset is None:
            base_queryset = Domain.objects

        return base_queryset.filter(builder=builder)

    def create_domain(self, builder: Builder, domain_name: str) -> Domain:
        """
        Creates a new domain

        :param builder: The builder the domain belongs to
        :param domain_name: The name of the domain
        :return: The newly created domain instance
        """

        last_order = Domain.get_last_order(builder)
        domain = Domain.objects.create(
            builder=builder, domain_name=domain_name, order=last_order
        )

        return domain

    def delete_domain(self, domain: Domain):
        """
        Deletes the domain provided

        :param domain: The domain that must be deleted
        """

        domain.delete()

    def update_domain(self, domain: Domain, **kwargs) -> Domain:
        """
        Updates fields of a domain

        :param domain: The domain that should be updated
        :param kwargs: The fields that should be updated with their corresponding value
        :return: The updated domain
        """

        for key, value in kwargs.items():
            setattr(domain, key, value)

        domain.save()

        return domain

    def order_domains(
        self, builder: Builder, order: List[int], base_qs=None
    ) -> List[int]:
        """
        Assigns a new order to the domains in a builder application.
        You can provide a base_qs for pre-filter the domains affected by this change.

        :param builder: The builder that the domains belong to
        :param order: The new order of the domains
        :param base_qs: A QS that can have filters already applied
        :raises DomainNotInBuilder: If the domain is not part of the provided builder
        :return: The new order of the domains
        """

        if base_qs is None:
            base_qs = Domain.objects.filter(builder=builder)

        try:
            full_order = Domain.order_objects(base_qs, order)
        except IdDoesNotExist as error:
            raise DomainNotInBuilder(error.not_existing_id)

        return full_order

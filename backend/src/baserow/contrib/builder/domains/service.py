from typing import List

from django.contrib.auth.models import AbstractUser

from baserow.contrib.builder.domains.handler import DomainHandler
from baserow.contrib.builder.domains.models import Domain
from baserow.contrib.builder.domains.operations import (
    CreateDomainOperationType,
    DeleteDomainOperationType,
    ReadDomainOperationType,
    UpdateDomainOperationType,
)
from baserow.contrib.builder.domains.signals import (
    domain_created,
    domain_deleted,
    domain_updated,
    domains_reordered,
)
from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.operations import OrderDomainsBuilderOperationType
from baserow.core.handler import CoreHandler
from baserow.core.utils import extract_allowed


class DomainService:
    def __init__(self):
        self.handler = DomainHandler()

    def get_domain(
        self, user: AbstractUser, domain_id: int, base_queryset=None
    ) -> Domain:
        """
        Gets a domain by ID

        :param user: The user requesting the domain
        :param domain_id: The ID of the domain
        :param base_queryset: Can be used to already apply changes to the qs used
        :return: The model instance of the Domain
        """

        base_queryset = base_queryset if base_queryset is not None else Domain.objects
        base_queryset = base_queryset.select_related("builder", "builder__workspace")
        domain = self.handler.get_domain(domain_id, base_queryset=base_queryset)

        CoreHandler().check_permissions(
            user,
            ReadDomainOperationType.type,
            workspace=domain.builder.workspace,
            context=domain,
        )

        return domain

    def create_domain(
        self, user: AbstractUser, builder: Builder, domain_name: str
    ) -> Domain:
        """
        Creates a new domain

        :param user: The user trying to create the domain
        :param builder: The builder the domain belongs to
        :param domain_name: The name of the domain
        :return: The newly created domain instance
        """

        CoreHandler().check_permissions(
            user,
            CreateDomainOperationType.type,
            workspace=builder.workspace,
            context=builder,
        )

        domain = self.handler.create_domain(builder, domain_name)

        domain_created.send(self, domain=domain, user=user)

        return domain

    def delete_domain(self, user: AbstractUser, domain: Domain):
        """
        Deletes the domain provided

        :param user: The user trying to delete the domain
        :param domain: The domain that must be deleted
        """

        CoreHandler().check_permissions(
            user,
            DeleteDomainOperationType.type,
            workspace=domain.builder.workspace,
            context=domain,
        )

        self.handler.delete_domain(domain)

        domain_deleted.send(
            self, builder=domain.builder, domain_id=domain.id, user=user
        )

    def update_domain(self, user: AbstractUser, domain: Domain, **kwargs) -> Domain:
        """
        Updates fields of a domain

        :param user: The user trying to update the domain
        :param domain: The domain that should be updated
        :param kwargs: The fields that should be updated with their corresponding value
        :return: The updated domain
        """

        CoreHandler().check_permissions(
            user,
            UpdateDomainOperationType.type,
            workspace=domain.builder.workspace,
            context=domain,
        )

        allowed_updates = extract_allowed(kwargs, ["domain_name"])

        self.handler.update_domain(domain, **allowed_updates)

        domain_updated.send(self, domain=domain, user=user)

        return domain

    def order_domains(
        self, user: AbstractUser, builder: Builder, order: List[int]
    ) -> List[int]:
        """
        Assigns a new order to the domains in a builder application.

        :param user: The user trying to order the domains
        :param builder: The builder that the domains belong to
        :param order: The new order of the domains
        :return: The new order of the domains
        """

        CoreHandler().check_permissions(
            user,
            OrderDomainsBuilderOperationType.type,
            workspace=builder.workspace,
            context=builder,
        )

        all_domains = Domain.objects.filter(builder_id=builder.id)
        user_domains = CoreHandler().filter_queryset(
            user,
            OrderDomainsBuilderOperationType.type,
            all_domains,
            workspace=builder.workspace,
            context=builder,
        )

        full_order = self.handler.order_domains(builder, order, user_domains)

        domains_reordered.send(self, builder=builder, order=full_order, user=user)

        return full_order

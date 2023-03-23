from typing import List

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.builder.api.domains.serializers import DomainSerializer
from baserow.contrib.builder.domains import signals as domain_signals
from baserow.contrib.builder.domains.models import Domain
from baserow.contrib.builder.domains.object_scopes import BuilderDomainObjectScopeType
from baserow.contrib.builder.domains.operations import ReadDomainOperationType
from baserow.contrib.builder.models import Builder
from baserow.core.utils import generate_hash
from baserow.ws.tasks import broadcast_to_group, broadcast_to_permitted_users


@receiver(domain_signals.domain_created)
def domain_created(sender, domain: Domain, user: AbstractUser, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_permitted_users.delay(
            domain.builder.workspace_id,
            ReadDomainOperationType.type,
            BuilderDomainObjectScopeType.type,
            domain.id,
            {"type": "domain_created", "domain": DomainSerializer(domain).data},
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(domain_signals.domain_updated)
def domain_updated(sender, domain: Domain, user: AbstractUser, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_permitted_users.delay(
            domain.builder.workspace_id,
            ReadDomainOperationType.type,
            BuilderDomainObjectScopeType.type,
            domain.id,
            {
                "type": "domain_updated",
                "domain": DomainSerializer(domain).data,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(domain_signals.domain_deleted)
def domain_deleted(
    sender, builder: Builder, domain_id: int, user: AbstractUser, **kwargs
):
    transaction.on_commit(
        lambda: broadcast_to_permitted_users.delay(
            builder.workspace_id,
            ReadDomainOperationType.type,
            BuilderDomainObjectScopeType.type,
            domain_id,
            {
                "type": "domain_deleted",
                "domain_id": domain_id,
                "builder_id": builder.id,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(domain_signals.domains_reordered)
def domain_reordered(
    sender, builder: Builder, order: List[int], user: AbstractUser, **kwargs
):
    # Hashing all values here to not expose real ids of domains a user might not have
    # access to
    order = [generate_hash(o) for o in order]
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            builder.workspace_id,
            {
                "type": "domains_reordered",
                # A user might also not have access to the builder itself
                "builder_id": generate_hash(builder.id),
                "order": order,
            },
            getattr(user, "web_socket_id", None),
        )
    )

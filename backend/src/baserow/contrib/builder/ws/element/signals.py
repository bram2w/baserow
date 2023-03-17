from typing import List

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.builder.api.elements.serializers import ElementSerializer
from baserow.contrib.builder.elements import signals as element_signals
from baserow.contrib.builder.elements.models import Element
from baserow.contrib.builder.elements.object_scopes import BuilderElementObjectScopeType
from baserow.contrib.builder.elements.operations import ReadElementOperationType
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.pages.models import Page
from baserow.core.utils import generate_hash
from baserow.ws.tasks import broadcast_to_group, broadcast_to_permitted_users


@receiver(element_signals.element_created)
def element_created(sender, element: Element, user: AbstractUser, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_permitted_users.delay(
            element.page.builder.workspace_id,
            ReadElementOperationType.type,
            BuilderElementObjectScopeType.type,
            element.id,
            {
                "type": "element_created",
                "element": element_type_registry.get_serializer(
                    element, ElementSerializer
                ).data,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(element_signals.element_updated)
def element_updated(sender, element: Element, user: AbstractUser, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_permitted_users.delay(
            element.page.builder.workspace_id,
            ReadElementOperationType.type,
            BuilderElementObjectScopeType.type,
            element.id,
            {
                "type": "element_updated",
                "element": element_type_registry.get_serializer(
                    element, ElementSerializer
                ).data,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(element_signals.element_deleted)
def element_deleted(sender, page: Page, element_id: int, user: AbstractUser, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_permitted_users.delay(
            page.builder.workspace_id,
            ReadElementOperationType.type,
            BuilderElementObjectScopeType.type,
            element_id,
            {
                "type": "element_deleted",
                "element_id": element_id,
                "page_id": page.id,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(element_signals.elements_reordered)
def element_reordered(
    sender, page: Page, order: List[int], user: AbstractUser, **kwargs
):
    # Hashing all values here to not expose real ids of elements a user might not have
    # access to
    order = [generate_hash(o) for o in order]
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            page.builder.workspace_id,
            {
                "type": "elements_reordered",
                # A user might also not have access to the page itself
                "page_id": generate_hash(page.id),
                "order": order,
            },
            getattr(user, "web_socket_id", None),
        )
    )

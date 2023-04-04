from typing import List

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.builder.api.pages.serializers import PageSerializer
from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.object_scopes import BuilderObjectScopeType
from baserow.contrib.builder.operations import ListPagesBuilderOperationType
from baserow.contrib.builder.pages import signals as page_signals
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.pages.object_scopes import BuilderPageObjectScopeType
from baserow.contrib.builder.pages.operations import ReadPageOperationType
from baserow.core.utils import generate_hash
from baserow.ws.tasks import broadcast_to_group, broadcast_to_permitted_users


@receiver(page_signals.page_created)
def page_created(sender, page: Page, user: AbstractUser, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_permitted_users.delay(
            page.builder.workspace_id,
            ReadPageOperationType.type,
            BuilderPageObjectScopeType.type,
            page.id,
            {"type": "page_created", "page": PageSerializer(page).data},
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(page_signals.page_updated)
def page_updated(sender, page: Page, user: AbstractUser, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_permitted_users.delay(
            page.builder.workspace_id,
            ReadPageOperationType.type,
            BuilderPageObjectScopeType.type,
            page.id,
            {
                "type": "page_updated",
                "page": PageSerializer(page).data,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(page_signals.page_deleted)
def page_deleted(sender, builder: Builder, page_id: int, user: AbstractUser, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_permitted_users.delay(
            builder.workspace_id,
            ListPagesBuilderOperationType.type,
            BuilderObjectScopeType.type,
            builder.id,
            {"type": "page_deleted", "page_id": page_id, "builder_id": builder.id},
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(page_signals.pages_reordered)
def page_reordered(
    sender, builder: Builder, order: List[int], user: AbstractUser, **kwargs
):
    # Hashing all values here to not expose real ids of pages a user might not have
    # access to
    order = [generate_hash(o) for o in order]
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            builder.workspace_id,
            {
                "type": "pages_reordered",
                # A user might also not have access to the builder itself
                "builder_id": generate_hash(builder.id),
                "order": order,
            },
            getattr(user, "web_socket_id", None),
        )
    )

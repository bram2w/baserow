from django.dispatch import receiver
from django.db import transaction

from baserow.api.groups.serializers import GroupSerializer, GroupUserGroupSerializer
from baserow.api.applications.serializers import get_application_serializer
from baserow.core import signals

from .tasks import broadcast_to_group, broadcast_to_users


@receiver(signals.group_created)
def group_created(sender, group, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            group.id,
            {"type": "group_created", "group": GroupSerializer(group).data},
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.group_updated)
def group_updated(sender, group, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            group.id,
            {
                "type": "group_updated",
                "group_id": group.id,
                "group": GroupSerializer(group).data,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.group_deleted)
def group_deleted(sender, group_id, group, group_users, user=None, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_users.delay(
            [u.id for u in group_users],
            {"type": "group_deleted", "group_id": group_id},
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.group_user_updated)
def group_user_updated(sender, group_user, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_users.delay(
            [group_user.user_id],
            {
                "type": "group_updated",
                "group_id": group_user.group_id,
                "group": GroupUserGroupSerializer(group_user).data,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.group_user_deleted)
def group_user_deleted(sender, group_user, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_users.delay(
            [group_user.user_id],
            {"type": "group_deleted", "group_id": group_user.group_id},
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.application_created)
def application_created(sender, application, user, type_name, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            application.group_id,
            {
                "type": "application_created",
                "application": get_application_serializer(application).data,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.application_updated)
def application_updated(sender, application, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            application.group_id,
            {
                "type": "application_updated",
                "application_id": application.id,
                "application": get_application_serializer(application).data,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.application_deleted)
def application_deleted(sender, application_id, application, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            application.group_id,
            {"type": "application_deleted", "application_id": application_id},
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.applications_reordered)
def applications_reordered(sender, group, order, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            group.id,
            {
                "type": "applications_reordered",
                "group_id": group.id,
                "order": order,
            },
            getattr(user, "web_socket_id", None),
        )
    )

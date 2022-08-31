from django.db import transaction
from django.dispatch import receiver

from baserow.api.applications.serializers import get_application_serializer
from baserow.api.groups.serializers import (
    GroupSerializer,
    GroupUserGroupSerializer,
    GroupUserSerializer,
)
from baserow.api.user.serializers import PublicUserSerializer
from baserow.core import signals
from baserow.core.handler import CoreHandler
from baserow.core.models import GroupUser

from .tasks import broadcast_to_group, broadcast_to_groups, broadcast_to_users


@receiver(signals.user_updated)
def user_updated(sender, performed_by, user, **kwargs):
    group_ids = list(
        GroupUser.objects.filter(user=user).values_list("group_id", flat=True)
    )

    transaction.on_commit(
        lambda: broadcast_to_groups.delay(
            group_ids,
            {"type": "user_updated", "user": PublicUserSerializer(user).data},
            getattr(performed_by, "web_socket_id", None),
        )
    )


@receiver(signals.user_deleted)
def user_deleted(sender, performed_by, user, **kwargs):
    group_ids = list(
        GroupUser.objects.filter(user=user).values_list("group_id", flat=True)
    )

    transaction.on_commit(
        lambda: broadcast_to_groups.delay(
            group_ids, {"type": "user_deleted", "user": PublicUserSerializer(user).data}
        )
    )


@receiver(signals.user_restored)
def user_restored(sender, performed_by, user, **kwargs):
    group_ids = list(
        GroupUser.objects.filter(user=user).values_list("group_id", flat=True)
    )

    transaction.on_commit(
        lambda: broadcast_to_groups.delay(
            group_ids,
            {"type": "user_restored", "user": PublicUserSerializer(user).data},
        )
    )


@receiver(signals.user_permanently_deleted)
def user_permanently_deleted(sender, user_id, group_ids, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_groups.delay(
            group_ids, {"type": "user_permanently_deleted", "user_id": user_id}
        )
    )


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


@receiver(signals.group_user_added)
def group_user_added(sender, group_user, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            group_user.group_id,
            {
                "type": "group_user_added",
                "id": group_user.id,
                "group_id": group_user.group_id,
                "group_user": GroupUserSerializer(group_user).data,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.group_user_updated)
def group_user_updated(sender, group_user, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            group_user.group_id,
            {
                "type": "group_user_updated",
                "id": group_user.id,
                "group_id": group_user.group_id,
                "group_user": GroupUserSerializer(group_user).data,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.group_user_deleted)
def group_user_deleted(sender, group_user_id, group_user, user, **kwargs):
    def broadcast_to_group_and_removed_user():
        payload = {
            "type": "group_user_deleted",
            "id": group_user_id,
            "group_id": group_user.group_id,
            "group_user": GroupUserSerializer(group_user).data,
        }
        broadcast_to_group.delay(
            group_user.group_id,
            payload,
            getattr(user, "web_socket_id", None),
        )
        broadcast_to_users.delay(
            [group_user.user_id],
            payload,
            getattr(user, "web_socket_id", None),
        )

    transaction.on_commit(broadcast_to_group_and_removed_user)


@receiver(signals.group_restored)
def group_restored(sender, group_user, user, **kwargs):
    groupuser_groups = (
        CoreHandler().get_groupuser_group_queryset().get(id=group_user.id)
    )
    transaction.on_commit(
        lambda: broadcast_to_users.delay(
            [group_user.user_id],
            {
                "type": "group_restored",
                "group_id": group_user.group_id,
                "group": GroupUserGroupSerializer(groupuser_groups).data,
                "applications": [
                    get_application_serializer(application).data
                    for application in group_user.group.application_set.select_related(
                        "content_type", "group"
                    ).all()
                ],
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.groups_reordered)
def groups_reordered(sender, group_ids, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_users.delay(
            [user.id],
            {"type": "groups_reordered", "group_ids": group_ids},
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(signals.application_created)
def application_created(sender, application, user, **kwargs):
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

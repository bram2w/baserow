from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

from baserow.core.handler import CoreHandler
from baserow.core.notifications.handler import NotificationHandler
from baserow.core.notifications.models import NotificationRecipient
from baserow.core.registries import OperationType

from .exceptions import NotificationDoesNotExist
from .operations import (
    ListNotificationsOperationType,
    MarkNotificationAsReadOperationType,
)

User = get_user_model()


class NotificationService:
    @classmethod
    def get_workspace_if_has_permissions_or_raise(
        cls, user: AbstractUser, workspace_id: int, permission_type: Type[OperationType]
    ):
        workspace = CoreHandler().get_workspace(workspace_id)

        CoreHandler().check_permissions(
            user, permission_type.type, workspace=workspace, context=workspace
        )
        return workspace

    @classmethod
    def list_notifications(cls, user, workspace_id: int):
        workspace = cls.get_workspace_if_has_permissions_or_raise(
            user, workspace_id, ListNotificationsOperationType
        )

        return NotificationHandler.list_notifications(user, workspace)

    @classmethod
    def get_notification(
        cls,
        user: AbstractUser,
        workspace_id: int,
        notification_id: int,
    ) -> NotificationRecipient:
        """
        Get notification

        :param user: The user on whose behalf the request is made.
        :param workspace_id: The workspace id to get the notification for.
        :param notification_id: The notification id to get.
        """

        workspace = cls.get_workspace_if_has_permissions_or_raise(
            user, workspace_id, ListNotificationsOperationType
        )

        try:
            notification = NotificationHandler.all_notifications_for_user(
                user, workspace
            ).get(notification_id=notification_id)
        except NotificationRecipient.DoesNotExist:
            raise NotificationDoesNotExist(
                f"Notification {notification_id} is not found."
            )
        return notification

    @classmethod
    def mark_notification_as_read(
        cls,
        user: AbstractUser,
        workspace_id: int,
        notification_id: int,
        read: bool = True,
    ) -> NotificationRecipient:
        cls.get_workspace_if_has_permissions_or_raise(
            user, workspace_id, MarkNotificationAsReadOperationType
        )

        notification = NotificationHandler.get_notification_by_id(user, notification_id)
        return NotificationHandler.mark_notification_as_read(user, notification, read)

    @classmethod
    def mark_all_notifications_as_read(cls, user: AbstractUser, workspace_id: int):
        """
        Marks all notifications as read for the given user and workspace and
        sends the all_notifications_marked_as_read signal.

        :param user: The user for which to mark all notifications as read.
        :param workspace_id: The workspace id for which to mark all
            notifications as read.
        """

        workspace = cls.get_workspace_if_has_permissions_or_raise(
            user, workspace_id, MarkNotificationAsReadOperationType
        )

        NotificationHandler.mark_all_notifications_as_read(user, workspace)

    @classmethod
    def clear_all_notifications(
        cls,
        user: AbstractUser,
        workspace_id: int,
    ):
        """
        Clears all notifications for the given user and workspace and sends the
        all_notifications_cleared signal.

        :param user: The user for which to clear all notifications.
        :param workspace_id: The workspace id for which to clear all
        """

        workspace = cls.get_workspace_if_has_permissions_or_raise(
            user, workspace_id, MarkNotificationAsReadOperationType
        )

        NotificationHandler.clear_all_notifications(user, workspace)

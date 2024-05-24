from typing import List

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.dispatch import receiver

from baserow.api.notifications.serializers import NotificationRecipientSerializer
from baserow.core.notifications.models import Notification, NotificationRecipient
from baserow.ws.tasks import broadcast_to_users

from .signals import (
    all_notifications_cleared,
    all_notifications_marked_as_read,
    notification_created,
    notification_marked_as_read,
)


@receiver(notification_created)
def notify_notification_created(
    sender,
    notification: Notification,
    notification_recipients: List[NotificationRecipient],
    **kwargs,
):
    """
    Sends a notification to the recipient of the notification.
    """

    send_to_all_users = notification.broadcast
    user_ids = [recipient.recipient_id for recipient in notification_recipients]

    # the data are the same for all the recipients, so just pick the first one.
    notification_data = notification_recipients[:1]

    transaction.on_commit(
        lambda: broadcast_to_users.delay(
            user_ids,
            {
                "type": "notifications_created",
                "notifications": NotificationRecipientSerializer(
                    notification_data, many=True
                ).data,
            },
            send_to_all_users=send_to_all_users,
        )
    )


@receiver(notification_marked_as_read)
def notify_notification_marked_as_read(
    sender,
    notification: Notification,
    notification_recipient: NotificationRecipient,
    user: AbstractUser,
    ignore_web_socket_id=None,
    **kwargs,
):
    """
    Notify the user that the notification has been marked as read.
    """

    transaction.on_commit(
        lambda: broadcast_to_users.delay(
            [user.id],
            {
                "type": "notification_marked_as_read",
                "notification": NotificationRecipientSerializer(
                    notification_recipient
                ).data,
            },
            ignore_web_socket_id,
        )
    )


@receiver(all_notifications_marked_as_read)
def notify_all_notifications_marked_as_read(sender, user: AbstractUser, **kwargs):
    """
    Notify the user that all notifications have been marked as read.
    """

    transaction.on_commit(
        lambda: broadcast_to_users.delay(
            [user.id],
            {"type": "all_notifications_marked_as_read"},
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(all_notifications_cleared)
def notify_all_notifications_cleared(sender, user: AbstractUser, **kwargs):
    """
    Notify the user that all notifications have been cleared.
    """

    transaction.on_commit(
        lambda: broadcast_to_users.delay(
            [user.id],
            {"type": "all_notifications_cleared"},
            getattr(user, "web_socket_id", None),
        )
    )

from typing import Any, Dict, List, Optional, Union

from django.contrib.auth.models import AbstractUser
from django.db.models import Count, OuterRef, Q, QuerySet, Subquery
from django.db.models.functions import Coalesce

from opentelemetry import trace

from baserow.core.models import Workspace
from baserow.core.notifications.tasks import send_queued_notifications_to_users
from baserow.core.telemetry.utils import baserow_trace
from baserow.core.utils import grouper, transaction_on_commit_if_not_already

from .exceptions import NotificationDoesNotExist
from .models import Notification, NotificationRecipient
from .signals import (
    all_notifications_cleared,
    all_notifications_marked_as_read,
    notification_created,
    notification_marked_as_read,
)

tracer = trace.get_tracer(__name__)


class NotificationHandler:
    @classmethod
    def _get_unread_broadcast_q(cls, user: AbstractUser) -> Q:
        user_broadcast = NotificationRecipient.objects.filter(
            broadcast=True, recipient=user
        )
        unread_broadcast = Q(broadcast=True, recipient=None) & ~Q(
            notification_id__in=user_broadcast.values("notification_id")
        )
        return unread_broadcast

    @classmethod
    @baserow_trace(tracer)
    def get_notification_by_id(
        cls, user: AbstractUser, notification_id: int
    ) -> NotificationRecipient:
        """
        Get a notification for the given user matching the given notification
        id.

        :param user: The user to get the notification for.
        :param notification_id: The id of the notification.
        :return: The notification recipient instance.
        :raises BaseNotificationDoesNotExist: When the notification with the
            given id does not exist or the given user is not a recipient for it.
        """

        return cls.get_notification_by(user, id=notification_id)

    @classmethod
    @baserow_trace(tracer)
    def get_notification_by(cls, user: AbstractUser, **kwargs) -> Notification:
        """
        Get a notification for the given user matching the given kwargs.

        :param user: The user to get the notification for.
        :return: The notification instance.
        :raises BaseNotificationDoesNotExist: When the notification with the
            given id does not exist or the given user is not a recipient for it.
        """

        unread_broadcast = cls._get_unread_broadcast_q(user)

        notification_ids = NotificationRecipient.objects.filter(
            Q(recipient=user, cleared=False) | unread_broadcast
        ).values("notification_id")

        try:
            return Notification.objects.filter(id__in=notification_ids, **kwargs).get()
        except Notification.DoesNotExist:
            raise NotificationDoesNotExist("Notification does not exist.")

    @classmethod
    @baserow_trace(tracer)
    def all_notifications_for_user(cls, user, workspace: Optional[Workspace] = None):
        workspace_filter = Q(workspace_id=None)
        if workspace:
            workspace_filter |= Q(workspace_id=workspace.id)

        direct = Q(broadcast=False, recipient=user, queued=False) & workspace_filter
        uncleared_broadcast = Q(broadcast=True, recipient=user, cleared=False)
        unread_broadcast = cls._get_unread_broadcast_q(user)

        return NotificationRecipient.objects.filter(
            direct | uncleared_broadcast | unread_broadcast
        )

    @classmethod
    @baserow_trace(tracer)
    def list_notifications(cls, user, workspace: Workspace):
        """
        Returns a list of notifications for the given user and workspace.
        Broadcast notifications recipients are missing for the unread notifications,
        so we need to return them excluding the ones the user has already cleared.


        :param user: The user to get the notifications for.
        :param workspace: The workspace to get the notifications for.
        :return: A list of notifications.
        """

        return cls.all_notifications_for_user(user, workspace).select_related(
            "notification", "notification__sender"
        )

    @classmethod
    @baserow_trace(tracer)
    def get_unread_notifications_count(
        cls, user: AbstractUser, workspace: Optional[Workspace] = None
    ) -> int:
        """
        Returns the number of unread notifications for the given user.

        :param user: The user to count the notifications for.
        :param workspace: The workspace to count the notifications for.
        :return: The number of unread notifications.
        """

        workspace_q = Q(workspace_id=None)
        if workspace:
            workspace_q |= Q(workspace_id=workspace.id)

        unread_direct = (
            Q(broadcast=False, recipient=user, read=False, cleared=False, queued=False)
            & workspace_q
        )
        unread_broadcast = cls._get_unread_broadcast_q(user)

        return NotificationRecipient.objects.filter(
            unread_direct | unread_broadcast
        ).count()

    @classmethod
    @baserow_trace(tracer)
    def annotate_workspaces_with_unread_notifications_count(
        cls, user: AbstractUser, workspace_queryset: QuerySet, outer_ref_key: str = "pk"
    ) -> QuerySet:
        """
        Annotates the given workspace queryset with the number of unread notifications
        for the given user.

        :param user: The user to count the notifications for.
        :param workspace_queryset: The workspace queryset to annotate.
        :param outer_ref_key: The key to use for the outer ref.
        :return: The annotated workspace queryset.
        """

        notification_qs = NotificationRecipient.objects.filter(
            recipient=user,
            workspace_id=OuterRef(outer_ref_key),
            broadcast=False,
            read=False,
            cleared=False,
            queued=False,
        )

        subquery = Subquery(
            notification_qs.values("workspace_id")
            .annotate(count=Count("id"))
            .values("count")
        )

        return workspace_queryset.annotate(
            unread_notifications_count=Coalesce(subquery, 0)
        )

    @classmethod
    @baserow_trace(tracer)
    def _get_missing_broadcast_entries_for_user(
        cls,
        user: AbstractUser,
    ) -> QuerySet[NotificationRecipient]:
        """
        Because broadcast entries are created for user only when they mark them
        as read or cleared, this function returns the missing broadcast entries
        for the given user.

        :param user: The user to get the notifications for.
        :return: The missing broadcast notification recipients for the given
            user.
        """

        unread_broadcasts = cls._get_unread_broadcast_q(user)

        return NotificationRecipient.objects.filter(unread_broadcasts)

    @classmethod
    @baserow_trace(tracer)
    def _create_missing_entries_for_broadcast_notifications_with_defaults(
        cls, user: AbstractUser, read=False, cleared=False, **kwargs
    ):
        """
        Broadcast entries might be missing because are created only when the
        user mark them as read or cleared, so let's create them and mark them as
        cleared so they don't show up anymore but also they are not recreated
        when the user clears all notifications again.

        :param user: The user to create the NotificationRecipient for.
        :param read: If True, the created NotificationRecipient will be marked as read.
        :param cleared: If True, the created NotificationRecipient will be marked as
            cleared.
        :param kwargs: Extra kwargs to pass to the NotificationRecipient constructor.
        :return: None
        """

        missing_broadcasts_entries = cls._get_missing_broadcast_entries_for_user(user)

        batch_size = 2500
        for missing_entries_chunk in grouper(batch_size, missing_broadcasts_entries):
            NotificationRecipient.objects.bulk_create(
                [
                    cls.construct_notification_recipient(
                        recipient_id=user.id,
                        notification=empty_entry,
                        read=read,
                        cleared=cleared,
                        **kwargs,
                    )
                    for empty_entry in missing_entries_chunk
                ],
                ignore_conflicts=True,
            )

    @classmethod
    @baserow_trace(tracer)
    def clear_all_notifications(
        cls,
        user: AbstractUser,
        workspace: Workspace,
    ):
        """
        Clears all the notifications for the given user and workspace. Broadcast
        notifications are cleared setting the cleared flag to True for the
        recipient. Direct notifications are cleared deleting the
        NotificationRecipient entries. If a direct notification ends up without
        recipients, it will be deleted as well.

        :param user: The user to clear the notifications for.
        :param workspace: The workspace to clear the notifications for.
        """

        cls._create_missing_entries_for_broadcast_notifications_with_defaults(
            user, cleared=True
        )

        # clear also read broadcast notifications
        NotificationRecipient.objects.filter(
            broadcast=True, recipient=user, cleared=False
        ).update(cleared=True)

        # direct notifications can be deleted if there are no more recipients
        uncleared_direct = NotificationRecipient.objects.filter(
            Q(workspace_id=workspace.pk) | Q(workspace_id=None),
            recipient=user,
            broadcast=False,
            cleared=False,
            queued=False,
        )

        Notification.objects.annotate(recipient_count=Count("recipients")).filter(
            Q(workspace_id=workspace.pk) | Q(workspace_id=None),
            broadcast=False,
            recipient_count=1,
            id__in=uncleared_direct.values("notification_id"),
        ).delete()

        # delete the ones that still have other recipients
        uncleared_direct.delete()

        all_notifications_cleared.send(sender=cls, user=user, workspace=workspace)

    @classmethod
    @baserow_trace(tracer)
    def mark_notification_as_read(
        cls,
        user: AbstractUser,
        notification: Notification,
        read: bool = True,
        include_user_in_signal: bool = False,
    ) -> NotificationRecipient:
        """
        Marks a notification as read for the given user and returns the updated
        notification instance.

        :param user: The user to mark the notifications as read for.
        :param notification: The notification to mark as read.
        :param read: If True, the notification will be marked as read, otherwise
            it will be marked as unread.
        :param include_user_in_signal: Since the notification can be
            automatically marked as read by the system, this parameter can be
            used to include the user session in the real time event.
        :return: The notification instance updated.
        """

        notification_recipient, _ = NotificationRecipient.objects.update_or_create(
            notification=notification,
            recipient=user,
            defaults={
                "read": read,
                "workspace_id": notification.workspace_id,
                "broadcast": notification.broadcast,
                "created_on": notification.created_on,
            },
        )

        # If the notification is marked as read by the system, then we
        # want to send the signal to the current websocket as well
        ignore_web_socket_id = getattr(user, "web_socket_id", None)
        if include_user_in_signal:
            ignore_web_socket_id = None

        notification_marked_as_read.send(
            sender=cls,
            notification=notification,
            notification_recipient=notification_recipient,
            user=user,
            ignore_web_socket_id=ignore_web_socket_id,
        )

        return notification_recipient

    @classmethod
    @baserow_trace(tracer)
    def mark_all_notifications_as_read(
        cls,
        user: AbstractUser,
        workspace: Workspace,
    ):
        """
        Marks all the notifications as read for the given workspace and user.

        :param user: The user to mark the notifications as read for.
        :param workspace: The workspace to filter the notifications by.
        """

        cls._create_missing_entries_for_broadcast_notifications_with_defaults(
            user, read=True
        )

        NotificationRecipient.objects.filter(
            Q(workspace_id=workspace.pk) | Q(workspace_id=None),
            recipient=user,
            read=False,
            cleared=False,
            queued=False,
        ).update(read=True)

        all_notifications_marked_as_read.send(
            sender=cls, user=user, workspace=workspace
        )

    @classmethod
    @baserow_trace(tracer)
    def construct_notification(
        cls, notification_type: str, sender=None, data=None, workspace=None, **kwargs
    ) -> Notification:
        """
        Create the notification with the provided data.

        :param notification_type: The type of the notification.
        :param sender: The user that sent the notification.
        :param data: The data that will be stored in the notification.
        :param workspace: The workspace that the notification is linked to.
        :return: The constructed notification instance. Be aware that this
            instance is not saved yet.
        """

        return Notification(
            type=notification_type,
            sender=sender,
            data=data or {},
            workspace=workspace,
            **kwargs,
        )

    @classmethod
    @baserow_trace(tracer)
    def construct_notification_recipient(
        cls,
        notification: Union[Notification, NotificationRecipient],
        recipient: Optional[AbstractUser] = None,
        read=False,
        cleared=False,
        queued=False,
        **kwargs,
    ) -> Notification:
        """
        Create the notification recpient with the provided data, copying
        necessary data from the provided notification.

        :param notification: The notification to reference and to copy data
            from.
        :param recipient: The user that the notification is for.
        :param read: If True, the notification will be marked as read.
        :param cleared: If True, the notification will be marked as cleared.
        :param queued: If True, the notification will be marked as queued.
        :param kwargs: Any additional data to be stored in the notification
            recipient.
        :return: The constructed notification recipient instance. Be aware that
            this instance is not saved yet.
        """

        # if another notification recipient is provided, then we can just copy the data
        if isinstance(notification, NotificationRecipient):
            kwargs["notification_id"] = notification.notification_id
        elif isinstance(notification, Notification):
            kwargs["notification"] = notification
        else:
            raise TypeError(
                "notification must be a Notification or NotificationRecipient "
                f"instance, not {type(notification)}"
            )

        return NotificationRecipient(
            recipient=recipient,
            created_on=notification.created_on,
            broadcast=notification.broadcast,
            workspace_id=notification.workspace_id,
            read=read,
            cleared=cleared,
            queued=queued,
            **kwargs,
        )

    @classmethod
    @baserow_trace(tracer)
    def create_notification(
        cls, notification_type: str, sender=None, data=None, workspace=None, **kwargs
    ) -> Notification:
        """
        Create the notification with the provided data.

        :param notification_type: The type of the notification.
        :param sender: The user that sent the notification.
        :param data: The data that will be stored in the notification.
        :param workspace: The workspace that the notification is linked to.
        :param save: If True the notification will be saved in the database.
        :return: The created notification instance.
        """

        notification = cls.construct_notification(
            notification_type=notification_type,
            sender=sender,
            data=data,
            workspace=workspace,
            **kwargs,
        )

        notification.save()

        return notification

    @classmethod
    @baserow_trace(tracer)
    def create_broadcast_notification(
        cls,
        notification_type: str,
        sender=None,
        data=None,
        **kwargs,
    ) -> Notification:
        """
        Create the notification with the provided data.

        :param notification_type: The type of the notification.
        :param sender: The user that sent the notification.
        :param data: The data that will be stored in the notification.
        :param workspace: The workspace that the notification is linked to.
        :param save: If True the notification will be saved in the database.
        :return: The created notification instance.
        """

        notification = cls.create_notification(
            notification_type=notification_type,
            sender=sender,
            data=data,
            workspace=None,
            broadcast=True,
            **kwargs,
        )

        # With recipient=None we create a placeholder recipient that will be
        # used to send the notification to all users.
        notification_recipient = cls.construct_notification_recipient(
            notification=notification, recipient=None
        )
        notification_recipient.save()

        notification_created.send(
            sender=cls,
            notification=notification,
            notification_recipients=[notification_recipient],
            user=sender,
        )

        return notification

    @classmethod
    @baserow_trace(tracer)
    def create_notification_for_users(
        cls,
        notification_type: str,
        recipients: List[AbstractUser],
        sender: Optional[AbstractUser] = None,
        data: Optional[Dict[str, Any]] = None,
        workspace: Optional[Workspace] = None,
        **kwargs,
    ) -> List[NotificationRecipient]:
        """
        Creates a notification for each user in the given list with the provided data.

        :param notification_type: The type of the notification.
        :param recipients: The users that will receive the notification.
        :param data: The data that will be stored in the notification.
        :param workspace: The workspace that the notification is linked to.
        :param kwargs: Any additional kwargs that will be passed to the
            Notification constructor.
        :return: A list of the created notification recipients instances.
        """

        notification = cls.create_notification(
            notification_type=notification_type,
            data=data,
            sender=sender,
            broadcast=False,
            workspace=workspace,
            **kwargs,
        )

        notification_recipients = NotificationRecipient.objects.bulk_create(
            [
                cls.construct_notification_recipient(
                    recipient=recipient, notification=notification
                )
                for recipient in recipients
            ]
        )

        notification_created.send(
            sender=cls,
            user=sender,
            notification=notification,
            notification_recipients=notification_recipients,
        )
        return notification_recipients


class UserNotificationsGrouper:
    """
    A utility class that aggregates notifications per user, enabling a single
    message delivery containing all the user's relevant notifications, rather
    than sending each notification individually.
    """

    def __init__(self):
        self.notifications: List[Notification] = []
        self.recipients_ids: List[List[int]] = []

    def has_notifications_to_send(self):
        return len(self.notifications) > 0

    def add(self, notification: Notification, recipient_ids: List[int]):
        self.recipients_ids.append(recipient_ids)
        self.notifications.append(notification)

    def create_all_notifications_and_trigger_task(self, batch_size=2500):
        created_instances = Notification.objects.bulk_create(
            self.notifications, batch_size=batch_size
        )

        notification_recipients = []
        for i, notification in enumerate(created_instances):
            notification_recipients.extend(
                [
                    NotificationHandler.construct_notification_recipient(
                        notification=notification,
                        recipient_id=recipient_id,
                        queued=True,
                    )
                    for recipient_id in self.recipients_ids[i]
                ]
            )

        NotificationRecipient.objects.bulk_create(
            notification_recipients, batch_size=batch_size, ignore_conflicts=True
        )
        transaction_on_commit_if_not_already(send_queued_notifications_to_users.delay)

    def user_grouper(self):
        while True:
            notification, recipients = yield
            self.add(notification, recipients)

    def __enter__(self):
        self.user_grouper = self.user_grouper()
        next(self.user_grouper)
        return self.user_grouper

    def __exit__(self, exc_type, exc_value, traceback):
        self.user_grouper.close()
        if exc_type is None:
            self.create_all_notifications_and_trigger_task()

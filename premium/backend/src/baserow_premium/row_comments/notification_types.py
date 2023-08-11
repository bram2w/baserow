from dataclasses import asdict, dataclass

from django.dispatch import receiver
from django.utils.translation import gettext as _

from baserow.core.notifications.handler import NotificationHandler
from baserow.core.notifications.registries import (
    EmailNotificationTypeMixin,
    NotificationType,
)
from baserow.core.prosemirror.utils import prosemirror_doc_to_plain_text

from .signals import row_comment_created, row_comment_updated


@dataclass
class RowCommentMentionNotificationData:
    database_id: int
    database_name: str
    table_id: int
    table_name: str
    row_id: int
    comment_id: int
    message: str

    @classmethod
    def from_row_comment(cls, row_comment):
        return cls(
            database_id=row_comment.table.database.id,
            database_name=row_comment.table.database.name,
            table_id=row_comment.table_id,
            table_name=row_comment.table.name,
            row_id=int(row_comment.row_id),
            comment_id=row_comment.id,
            message=row_comment.message,
        )


class RowCommentMentionNotificationType(EmailNotificationTypeMixin, NotificationType):
    type = "row_comment_mention"

    @classmethod
    def notify_mentioned_users(cls, row_comment, mentions):
        """
        Creates a notification for each user that is mentioned in the comment.

        :param row_comment: The comment that was created.
        :param mentions: The list of users that are mentioned.
        :return: The list of created notifications.
        """

        notification_data = RowCommentMentionNotificationData.from_row_comment(
            row_comment
        )
        NotificationHandler.create_direct_notification_for_users(
            notification_type=cls.type,
            recipients=mentions,
            data=asdict(notification_data),
            sender=row_comment.user,
            workspace=row_comment.table.database.workspace,
        )

    @classmethod
    def get_notification_title_for_email(cls, notification, context):
        return _("%(user)s mentioned you in row %(row_id)s in %(table_name)s.") % {
            "user": notification.sender.first_name,
            "row_id": notification.data["row_id"],
            "table_name": notification.data["table_name"],
        }

    @classmethod
    def get_notification_description_for_email(cls, notification, context):
        return prosemirror_doc_to_plain_text(notification.data["message"])


@receiver(row_comment_created)
def on_row_comment_created(sender, row_comment, user, mentions, **kwargs):
    if mentions:
        RowCommentMentionNotificationType.notify_mentioned_users(row_comment, mentions)


@receiver(row_comment_updated)
def on_row_comment_updated(sender, row_comment, user, mentions, **kwargs):
    if mentions:
        RowCommentMentionNotificationType.notify_mentioned_users(row_comment, mentions)

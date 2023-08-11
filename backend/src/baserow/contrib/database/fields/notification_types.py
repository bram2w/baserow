from dataclasses import asdict, dataclass
from itertools import chain
from typing import TYPE_CHECKING

from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from django.utils.translation import gettext as _

from baserow.contrib.database.fields.field_types import MultipleCollaboratorsFieldType
from baserow.contrib.database.rows.handler import RowM2MChangeTracker
from baserow.contrib.database.rows.signals import rows_created, rows_updated
from baserow.core.notifications.handler import (
    NotificationHandler,
    UserNotificationsGrouper,
)
from baserow.core.notifications.registries import (
    EmailNotificationTypeMixin,
    NotificationType,
)

if TYPE_CHECKING:
    from baserow.contrib.database.fields.models import Field
    from baserow.contrib.database.table.models import GeneratedTableModel


@dataclass
class CollaboratorAddedToRowNotificationData:
    database_id: int
    database_name: str
    table_id: int
    table_name: str
    field_id: int
    field_name: str
    row_id: int


class CollaboratorAddedToRowNotificationType(
    EmailNotificationTypeMixin, NotificationType
):
    type = "collaborator_added_to_row"

    @classmethod
    def get_notification_title_for_email(cls, notification, context):
        return _(
            "%(sender)s assigned you to %(field_name)s in row %(row_id)s in %(table_name)s."
        ) % {
            "sender": notification.sender.first_name,
            "field_name": notification.data["field_name"],
            "row_id": notification.data["row_id"],
            "table_name": notification.data["table_name"],
        }

    @classmethod
    def get_notification_description_for_email(cls, notification, context):
        return None

    @classmethod
    def construct_notification(
        cls, sender: AbstractUser, row: "GeneratedTableModel", field: "Field"
    ):
        """
        Notifies the given users that they have been added to the given row.

        :param user: The user that added the given users to the row.
        :param collaborators_to_notify: The users that have been added to the row.
        :param row: The row that the users have been added to.
        :param field: The field that the users have been added to.
        """

        table = row.baserow_table
        workspace = table.database.workspace
        data = CollaboratorAddedToRowNotificationData(
            row_id=row.id,
            field_id=field.id,
            field_name=field.name,
            table_id=table.id,
            table_name=table.name,
            database_id=table.database.id,
            database_name=table.database.name,
        )

        return NotificationHandler.construct_notification(
            cls.type, data=asdict(data), sender=sender, workspace=workspace
        )

    @classmethod
    def _iter_field_row_and_collaborators_to_notify(
        cls, m2m_change_tracker: RowM2MChangeTracker
    ):
        field_rows_and_collaborators_to_notify = {
            field: row_and_collaborators_to_notify
            for field, row_and_collaborators_to_notify in m2m_change_tracker.get_created_m2m_rels_per_field_for_type(
                MultipleCollaboratorsFieldType.type
            ).items()
            if field.notify_user_when_added
        }

        return chain.from_iterable(
            (
                (field, row, collaborators_to_notify)
                for row, collaborators_to_notify in row_and_collaborators_to_notify.items()
                if collaborators_to_notify
            )
            for field, row_and_collaborators_to_notify in field_rows_and_collaborators_to_notify.items()
        )

    @classmethod
    def create_notifications_grouped_by_user(
        cls, user: AbstractUser, m2m_change_tracker: RowM2MChangeTracker
    ):
        """
        Creates notifications grouped by user for the given rows and
        collaborator fields. It uses the UserNotificationsGrouper to group the
        notifications by user and trigger the task to send the notifications
        for each user at the end.

        :param user: The user that added the given users to the row.
        :param m2m_change_tracker: A change tracker containing all changes to m2m
            relationships that just occurred, so we can create any needed notification.
        """

        notification_grouper = UserNotificationsGrouper()

        iterator = cls._iter_field_row_and_collaborators_to_notify(m2m_change_tracker)
        for field, row, collaborators_to_notify in iterator:
            notification = cls.construct_notification(sender=user, row=row, field=field)
            notification_grouper.add(notification, list(collaborators_to_notify))

        if notification_grouper.has_notifications_to_send():
            notification_grouper.create_all_notifications_and_trigger_task()


@receiver(rows_created)
def notify_users_added_to_row_when_rows_created(
    sender,
    rows,
    before,
    user,
    table,
    model,
    send_realtime_update=True,
    send_webhook_events=True,
    m2m_change_tracker=None,
    **kwargs
):
    if m2m_change_tracker is not None:
        CollaboratorAddedToRowNotificationType.create_notifications_grouped_by_user(
            user, m2m_change_tracker
        )


@receiver(rows_updated)
def notify_users_added_to_row_when_rows_updated(
    sender,
    rows,
    user,
    table,
    model,
    before_return,
    updated_field_ids,
    before_rows_values,
    m2m_change_tracker=None,
    **kwargs
):
    if m2m_change_tracker is not None:
        CollaboratorAddedToRowNotificationType.create_notifications_grouped_by_user(
            user, m2m_change_tracker
        )

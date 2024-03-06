from dataclasses import asdict, dataclass
from itertools import chain
from typing import TYPE_CHECKING, List

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
    row_name: str


class CollaboratorAddedToRowNotificationType(
    EmailNotificationTypeMixin, NotificationType
):
    type = "collaborator_added_to_row"

    @classmethod
    def get_notification_title_for_email(cls, notification, context):
        return _(
            "%(sender)s assigned you to %(field_name)s in row %(row_name)s in %(table_name)s."
        ) % {
            "sender": notification.sender.first_name,
            "field_name": notification.data["field_name"],
            "row_name": notification.data.get("row_name", notification.data["row_id"]),
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

        :param sender: The user that added the given users to the row.
        :param row: The row that the users have been added to.
        :param field: The field that the users have been added to.
        """

        table = row.baserow_table
        workspace = table.database.workspace
        data = CollaboratorAddedToRowNotificationData(
            row_id=row.id,
            row_name=str(row),
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
        cls,
        m2m_change_tracker: RowM2MChangeTracker,
        updated_rows: List["GeneratedTableModel"],
    ):
        # The row provided by the iterator might not have all the updated values in
        # case of a bulk row update. This is because some fields require a returning
        # value after insert or update, but the `bulk_update` in the `create_rows`
        # method doesn't update these computed properties, so this row might have a
        # raw expression instead of the computed output. We're therefore replacing the
        # row from the updated set.
        row_id_map = {row.id: row for row in updated_rows}

        field_rows_and_collaborators_to_notify = {
            field: row_and_collaborators_to_notify
            for field, row_and_collaborators_to_notify in m2m_change_tracker.get_created_m2m_rels_per_field_for_type(
                MultipleCollaboratorsFieldType.type
            ).items()
            if field.notify_user_when_added
        }

        return chain.from_iterable(
            (
                (field, row_id_map[row.id], collaborators_to_notify)
                for row, collaborators_to_notify in row_and_collaborators_to_notify.items()
                if collaborators_to_notify
            )
            for field, row_and_collaborators_to_notify in field_rows_and_collaborators_to_notify.items()
        )

    @classmethod
    def create_notifications_grouped_by_user(
        cls,
        user: AbstractUser,
        m2m_change_tracker: RowM2MChangeTracker,
        rows: List["GeneratedTableModel"],
    ):
        """
        Creates notifications grouped by user for the given rows and
        collaborator fields. It uses the UserNotificationsGrouper to group the
        notifications by user and trigger the task to send the notifications
        for each user at the end.

        :param user: The user that added the given users to the row.
        :param m2m_change_tracker: A change tracker containing all changes to m2m
            relationships that just occurred, so we can create any needed notification.
        :param rows: A list containing all the updated rows in the latest version.
            The ones in the m2m_change_tracker might not be up-to-date because the
            `bulk_update` function from Django doesn't get return the computed values.
        """

        notification_grouper = UserNotificationsGrouper()

        iterator = cls._iter_field_row_and_collaborators_to_notify(
            m2m_change_tracker, rows
        )
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
            user, m2m_change_tracker, rows
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
            user, m2m_change_tracker, rows
        )

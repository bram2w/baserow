from dataclasses import asdict, dataclass

from django.dispatch import receiver

from baserow.core.notifications.exceptions import NotificationDoesNotExist
from baserow.core.notifications.handler import NotificationHandler
from baserow.core.notifications.registries import NotificationType

from .signals import (
    workspace_invitation_accepted,
    workspace_invitation_created,
    workspace_invitation_rejected,
)


@dataclass
class InvitationNotificationData:
    invitation_id: int
    invited_to_workspace_id: int
    invited_to_workspace_name: str


def mark_invitation_notification_as_read(user, invitation):
    try:
        notification = NotificationHandler.get_notification_by(
            user,
            notificationrecipient__read=False,
            data__contains={"invitation_id": invitation.id},
        )
    except NotificationDoesNotExist:
        return

    NotificationHandler.mark_notification_as_read(
        user, notification, include_user_in_signal=True
    )


class WorkspaceInvitationCreatedNotificationType(NotificationType):
    type = "workspace_invitation_created"

    @classmethod
    def create_invitation_created_notification(cls, invitation, invited_user):
        NotificationHandler.create_notification_for_users(
            notification_type=cls.type,
            recipients=[invited_user],
            sender=invitation.invited_by,
            data=asdict(
                InvitationNotificationData(
                    invitation.id, invitation.workspace.id, invitation.workspace.name
                )
            ),
        )


@receiver(workspace_invitation_created)
def handle_workspace_invitation_created(
    sender, invitation, invited_user=None, **kwargs
):
    if invited_user:
        WorkspaceInvitationCreatedNotificationType.create_invitation_created_notification(
            invitation, invited_user
        )


class WorkspaceInvitationAcceptedNotificationType(NotificationType):
    type = "workspace_invitation_accepted"

    @classmethod
    def create_invitation_accepted_notification(cls, user, invitation):
        NotificationHandler.create_notification_for_users(
            notification_type=cls.type,
            recipients=[invitation.invited_by],
            sender=user,
            data=asdict(
                InvitationNotificationData(
                    invitation.id, invitation.workspace.id, invitation.workspace.name
                )
            ),
            workspace=invitation.workspace,
        )


@receiver(workspace_invitation_accepted)
def handle_workspace_invitation_accepted(sender, invitation, user, **kwargs):
    mark_invitation_notification_as_read(user, invitation)
    WorkspaceInvitationAcceptedNotificationType.create_invitation_accepted_notification(
        user, invitation
    )


class WorkspaceInvitationRejectedNotificationType(NotificationType):
    type = "workspace_invitation_rejected"

    @classmethod
    def create_invitation_rejected_notification(cls, user, invitation):
        NotificationHandler.create_notification_for_users(
            notification_type=cls.type,
            recipients=[invitation.invited_by],
            sender=user,
            data=asdict(
                InvitationNotificationData(
                    invitation.id, invitation.workspace.id, invitation.workspace.name
                )
            ),
            workspace=invitation.workspace,
        )


@receiver(workspace_invitation_rejected)
def handle_workspace_invitation_rejected(sender, invitation, user, **kwargs):
    mark_invitation_notification_as_read(user, invitation)
    WorkspaceInvitationRejectedNotificationType.create_invitation_rejected_notification(
        user, invitation
    )


class BaserowVersionUpgradeNotificationType(NotificationType):
    type = "baserow_version_upgrade"

    @classmethod
    def create_version_upgrade_broadcast_notification(
        cls, version, release_notes_url=None
    ):
        NotificationHandler.create_broadcast_notification(
            notification_type=cls.type,
            sender=None,
            data={"version": version, "release_notes_url": release_notes_url},
        )

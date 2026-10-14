from dataclasses import asdict, dataclass
from typing import Optional

from baserow.core.notifications.handler import NotificationHandler
from baserow.core.notifications.registries import (
    EmailNotificationTypeMixin,
    NotificationType,
)

from .models import AgentChat, AgentFollowUp


@dataclass
class AgentFollowUpNotificationData:
    follow_up_id: int
    application_id: int
    agent_name: str
    title: str
    message: str
    status: str
    # The check that found it, opened when the notification is clicked.
    chat_uuid: Optional[str]


class AgentFollowUpNotificationType(EmailNotificationTypeMixin, NotificationType):
    """
    What a follow-up tells the user who asked for it: something changed, it
    completed, or it stopped.
    """

    type = "agent_follow_up"
    has_web_frontend_route = True

    @classmethod
    def notify(
        cls, follow_up: AgentFollowUp, chat: Optional[AgentChat], message: str
    ) -> None:
        application = follow_up.application
        data = AgentFollowUpNotificationData(
            follow_up_id=follow_up.id,
            application_id=application.id,
            agent_name=application.name,
            title=follow_up.title,
            message=message[:2000],
            status=follow_up.status,
            chat_uuid=str(chat.uuid) if chat is not None else None,
        )
        NotificationHandler.create_direct_notification_for_users(
            notification_type=cls.type,
            recipients=[follow_up.created_by],
            data=asdict(data),
            sender=None,
            workspace=application.workspace,
        )

    @classmethod
    def get_notification_title_for_email(cls, notification, context) -> str:
        return "%(agent)s: %(title)s" % {
            "agent": notification.data.get("agent_name", ""),
            "title": notification.data.get("title", ""),
        }

    @classmethod
    def get_notification_description_for_email(
        cls, notification, context
    ) -> Optional[str]:
        return notification.data.get("message") or None

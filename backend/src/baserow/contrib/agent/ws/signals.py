from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.agent.models import AgentConversation
from baserow.contrib.agent.signals import agent_conversation_updated
from baserow.ws.tasks import broadcast_to_users


@receiver(agent_conversation_updated)
def conversation_updated(
    sender, conversation: AgentConversation, user: AbstractUser, **kwargs
):
    """Refresh only the owner's other sessions, without broadcasting private content."""

    payload = {
        "type": "agent_conversation_updated",
        "agent_id": conversation.agent_id,
        "conversation_uuid": str(conversation.uuid),
    }
    owner_id = conversation.owner_user_id
    web_socket_id = getattr(user, "web_socket_id", None)
    transaction.on_commit(
        lambda: broadcast_to_users.delay(
            [owner_id], payload, ignore_web_socket_id=web_socket_id
        )
    )

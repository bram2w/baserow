from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver

from baserow.contrib.agent.last_viewed_types import AgentLastViewedItemType
from baserow.contrib.agent.signals import agent_loaded
from baserow.core.last_viewed.handler import LastViewedHandler


@receiver(agent_loaded)
def agent_loaded_mark_last_viewed(
    sender, agent_id: int, user: AbstractUser, **kwargs
) -> None:
    LastViewedHandler.schedule_mark_viewed(user, AgentLastViewedItemType.type, agent_id)

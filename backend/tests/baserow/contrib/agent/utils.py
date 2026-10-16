from django.urls import reverse

from baserow.core.models import Application


def agent_url(agent: Application, view: str, **kwargs: object) -> str:
    return reverse(f"api:agent:{view}", kwargs={"agent_id": agent.id, **kwargs})

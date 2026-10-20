from dataclasses import dataclass
from typing import Literal, TypedDict

from .models import AgentApplication

AgentReadinessState = Literal["ready", "incomplete", "unavailable"]


class AgentConfiguration(TypedDict):
    state: AgentReadinessState
    instructions: str
    provider_type: str | None
    model_identifier: str | None
    errors: dict[str, str]


@dataclass
class AgentConfigurationUpdated:
    agent: AgentApplication
    changed_fields: list[str]
    configuration: AgentConfiguration

from dataclasses import dataclass

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from baserow.core.action.registries import (
    ActionScopeStr,
    ActionType,
    ActionTypeDescription,
)
from baserow.core.action.scopes import ApplicationActionScopeType

from .service import AgentService
from .types import AgentConfiguration


class UpdateAgentConfigurationActionType(ActionType):
    type = "update_agent_configuration"
    description = ActionTypeDescription(
        _("Update agent configuration"),
        _("Configuration updated for agent (%(agent_id)s)."),
    )
    analytics_params = ["agent_id", "changed_fields"]

    @dataclass
    class Params:
        agent_id: int
        changed_fields: list[str]

    @classmethod
    @transaction.atomic
    def do(
        cls, user: AbstractUser, agent_id: int, **values: str | None
    ) -> AgentConfiguration:
        """
        Update the configuration and audit the changed field names, never values.

        :param user: The user updating the configuration.
        :param agent_id: The id of the Agent.
        :param values: The configuration values to set, by field name.
        :return: The resulting configuration.
        """

        updated = AgentService().update_configuration(user, agent_id, **values)
        if updated.changed_fields:
            cls.register_action(
                user,
                cls.Params(agent_id, updated.changed_fields),
                cls.scope(agent_id),
                updated.agent.workspace,
            )
        return updated.configuration

    @classmethod
    def scope(cls, agent_id: int) -> ActionScopeStr:
        return ApplicationActionScopeType.value(agent_id)

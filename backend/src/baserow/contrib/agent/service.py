from django.contrib.auth.models import AbstractUser
from django.db import transaction

from baserow.core.handler import CoreHandler
from baserow.core.operations import UpdateApplicationOperationType
from baserow.core.signals import application_updated

from .handler import AgentHandler
from .models import AgentApplication
from .operations import ReadAgentConfigurationOperationType
from .types import AgentConfiguration, AgentConfigurationUpdated


class AgentService:
    def __init__(self):
        self.handler = AgentHandler()

    def _get_authorized_agent(
        self,
        user: AbstractUser,
        agent_id: int,
        *operations: str,
        for_update: bool = False,
    ) -> AgentApplication:
        """Fetch the Agent and check each operation on it."""

        agent = self.handler.get_agent(agent_id, for_update=for_update)
        for operation in operations:
            CoreHandler().check_permissions(
                user, operation, workspace=agent.workspace, context=agent
            )
        return agent

    def get_configuration(
        self, user: AbstractUser, agent_id: int
    ) -> AgentConfiguration:
        """
        Return the Agent configuration to a user allowed to read it.

        :param user: The user reading the configuration.
        :param agent_id: The id of the Agent.
        :raises PermissionException: When the user may not read the configuration.
        :return: The configuration values with their readiness.
        """

        agent = self._get_authorized_agent(
            user, agent_id, ReadAgentConfigurationOperationType.type
        )
        return self.handler.get_configuration(agent)

    @transaction.atomic
    def update_configuration(
        self, user: AbstractUser, agent_id: int, **values: str | None
    ) -> AgentConfigurationUpdated:
        """
        Save part of the configuration for a user who may update and read it.

        :param user: The user updating the configuration.
        :param agent_id: The id of the Agent.
        :param values: The configuration values to set, by field name.
        :raises PermissionException: When the user may not update the Agent or read
            its configuration.
        :return: The Agent, the names of the fields that changed and the resulting
            configuration.
        """

        agent = self._get_authorized_agent(
            user,
            agent_id,
            UpdateApplicationOperationType.type,
            ReadAgentConfigurationOperationType.type,
            for_update=True,
        )
        updated = self.handler.update_configuration(agent, **values)
        if updated.changed_fields:
            # Open pages refresh readiness from this public application payload.
            application_updated.send(self, application=agent, user=user)
        return updated

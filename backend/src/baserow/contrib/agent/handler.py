from baserow.core.ai_provider.constants import AI_PROVIDER_FEATURE_AI_AGENT
from baserow.core.ai_provider.resolution import ScopedAIProviderState
from baserow.core.generative_ai.registries import generative_ai_model_type_registry
from baserow.core.handler import CoreHandler
from baserow.core.utils import extract_allowed

from .models import AgentApplication
from .types import AgentConfiguration, AgentConfigurationUpdated
from .validators import validate_configuration_values


class AgentHandler:
    configuration_fields = ["instructions", "provider_type", "model_identifier"]

    def get_agent(self, agent_id: int, for_update: bool = False) -> AgentApplication:
        """
        Fetch an Agent that belongs to a workspace.

        :param agent_id: The id of the Agent.
        :param for_update: Whether to lock the Agent until the transaction ends.
        :raises ApplicationDoesNotExist: When the Agent doesn't exist, is trashed or
            has no workspace.
        :return: The Agent.
        """

        queryset = AgentApplication.objects.filter(workspace__isnull=False)
        if for_update:
            # Lock the parent first to match normal application updates.
            CoreHandler().get_application(
                agent_id,
                base_queryset=queryset.select_for_update(of=("application_ptr",)),
            )
            queryset = queryset.select_for_update(of=("self",))
        return CoreHandler().get_application(agent_id, base_queryset=queryset)

    def get_configuration(
        self,
        agent: AgentApplication,
        provider_state: ScopedAIProviderState | None = None,
    ) -> AgentConfiguration:
        """
        Return the configuration, its readiness and each blocking field error.

        :param agent: The Agent to read.
        :param provider_state: The AI provider state of the Agent's workspace, when
            the caller already loaded it.
        :return: The configuration values, the readiness state and the error of
            each field that keeps the Agent from being ready.
        """

        errors = {}
        for field in self.configuration_fields:
            if not (getattr(agent, field) or "").strip():
                errors[field] = "required"

        models = generative_ai_model_type_registry.get_enabled_models_per_type(
            agent.workspace,
            feature_type=AI_PROVIDER_FEATURE_AI_AGENT,
            state=provider_state,
        )
        if agent.provider_type:
            if agent.provider_type not in models:
                errors["provider_type"] = "unavailable"
            if agent.model_identifier and agent.model_identifier not in models.get(
                agent.provider_type, []
            ):
                errors["model_identifier"] = "unavailable"

        if "required" in errors.values():
            state = "incomplete"
        elif errors:
            state = "unavailable"
        else:
            state = "ready"
        return {
            **{field: getattr(agent, field) for field in self.configuration_fields},
            "state": state,
            "errors": errors,
        }

    def update_configuration(
        self, agent: AgentApplication, **values: str | None
    ) -> AgentConfigurationUpdated:
        """
        Save part of the configuration, accepting blank values as a draft.

        :param agent: The Agent to update.
        :param values: The configuration values to set, by field name. Other names
            are ignored.
        :return: The Agent, the names of the fields that changed and the resulting
            configuration.
        """

        values = extract_allowed(values, self.configuration_fields)
        validate_configuration_values(values)
        changed_fields = []
        for field, value in values.items():
            if field in ("provider_type", "model_identifier"):
                value = (value or "").strip() or None
            if getattr(agent, field) != value:
                setattr(agent, field, value)
                changed_fields.append(field)
        if changed_fields:
            agent.save(update_fields=[*changed_fields, "updated_on"])
        return AgentConfigurationUpdated(
            agent, changed_fields, self.get_configuration(agent)
        )

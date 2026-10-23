from django.apps import AppConfig


class AgentConfig(AppConfig):
    name = "baserow.contrib.agent"

    def ready(self):
        from baserow.core.action.registries import action_type_registry
        from baserow.core.registries import (
            application_type_registry,
            last_viewed_item_type_registry,
            operation_type_registry,
        )
        from baserow.core.search.registries import workspace_search_registry

        from .actions import UpdateAgentConfigurationActionType
        from .application_types import AgentApplicationType
        from .last_viewed_types import AgentLastViewedItemType
        from .operations import ReadAgentConfigurationOperationType
        from .search_types import AgentSearchType

        application_type_registry.register(AgentApplicationType())
        workspace_search_registry.register(AgentSearchType())
        last_viewed_item_type_registry.register(AgentLastViewedItemType())
        operation_type_registry.register(ReadAgentConfigurationOperationType())
        action_type_registry.register(UpdateAgentConfigurationActionType())

        import baserow.contrib.agent.receivers  # noqa: F401

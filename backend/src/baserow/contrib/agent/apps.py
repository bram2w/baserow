from django.apps import AppConfig


class AgentConfig(AppConfig):
    name = "baserow.contrib.agent"

    def ready(self):
        from baserow.core.registries import (
            application_type_registry,
            last_viewed_item_type_registry,
        )
        from baserow.core.search.registries import workspace_search_registry

        from .application_types import AgentApplicationType
        from .last_viewed_types import AgentLastViewedItemType
        from .search_types import AgentSearchType

        application_type_registry.register(AgentApplicationType())
        workspace_search_registry.register(AgentSearchType())
        last_viewed_item_type_registry.register(AgentLastViewedItemType())

        import baserow.contrib.agent.receivers  # noqa: F401

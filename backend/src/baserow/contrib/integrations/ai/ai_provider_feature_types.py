from baserow.core.ai_provider.constants import AI_PROVIDER_FEATURE_AI_AGENT
from baserow.core.ai_provider.registries import AIProviderModelFeatureType
from baserow.core.ai_provider.resolution import ScopedAIProviderState
from baserow.core.generative_ai.registries import generative_ai_model_type_registry
from baserow.core.models import Workspace


class AIAgentAIProviderModelFeatureType(AIProviderModelFeatureType):
    type = AI_PROVIDER_FEATURE_AI_AGENT

    def get_workspace_availability(
        self,
        workspace: Workspace | None,
        state: ScopedAIProviderState | None = None,
    ) -> dict[str, bool | dict[str, list[str]]]:
        """
        Return the providers and models available to AI Agent consumers.

        :param workspace: The workspace to resolve, or None for instance scope.
        :param state: Optional provider state already loaded for the same scope.
        :returns: Whether any eligible models exist and their identifiers grouped
            by provider type.
        """

        models = generative_ai_model_type_registry.get_enabled_models_per_type(
            workspace, feature_type=self.type, state=state
        )
        return {"is_enabled": bool(models), "models": models}

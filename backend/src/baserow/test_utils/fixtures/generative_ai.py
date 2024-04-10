from baserow.api.generative_ai.serializers import GenerativeAIModelsSerializer
from baserow.core.generative_ai.exceptions import GenerativeAIPromptError


class GenerativeAIFixtures:
    def register_fake_generate_ai_type(self, **kwargs):
        from baserow.core.generative_ai.registries import (
            GenerativeAIModelType,
            generative_ai_model_type_registry,
        )

        class TestGenerativeAINoModelType(GenerativeAIModelType):
            type = "test_generative_ai_no_model"

            def is_enabled(self, workspace=None):
                return False

            def get_enabled_models(self, workspace=None):
                return []

            def prompt(self, model, prompt, workspace=None):
                return ""

            def get_settings_serializer(self):
                return GenerativeAIModelsSerializer

        class TestGenerativeAIModelType(GenerativeAIModelType):
            type = "test_generative_ai"

            def is_enabled(self, workspace=None):
                return True

            def get_enabled_models(self, workspace=None):
                models = self.get_workspace_setting(workspace, "models")
                return models if models else ["test_1"]

            def prompt(self, model, prompt, workspace=None):
                return f"Generated: {prompt}"

            def get_settings_serializer(self):
                return GenerativeAIModelsSerializer

        class TestGenerativeAIModelTypePromptError(GenerativeAIModelType):
            type = "test_generative_ai_prompt_error"

            def is_enabled(self, workspace=None):
                return True

            def get_enabled_models(self, workspace=None):
                return ["test_1"]

            def prompt(self, model, prompt, workspace=None):
                raise GenerativeAIPromptError("Test error")

            def get_settings_serializer(self):
                return GenerativeAIModelsSerializer

        try:
            generative_ai_model_type_registry.register(TestGenerativeAINoModelType())
            generative_ai_model_type_registry.register(TestGenerativeAIModelType())
            generative_ai_model_type_registry.register(
                TestGenerativeAIModelTypePromptError()
            )
        except generative_ai_model_type_registry.already_registered_exception_class:
            pass

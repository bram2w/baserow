from baserow.core.generative_ai.exceptions import GenerativeAIPromptError


class GenerativeAIFixtures:
    def register_fake_generate_ai_type(self, **kwargs):
        from baserow.core.generative_ai.registries import (
            GenerativeAIModelType,
            generative_ai_model_type_registry,
        )

        class TestGenerativeAINoModelType(GenerativeAIModelType):
            type = "test_generative_ai_no_model"

            def is_enabled(self):
                return True

            def get_enabled_models(self):
                return []

            def prompt(self, model, prompt):
                return ""

        class TestGenerativeAIModelType(GenerativeAIModelType):
            type = "test_generative_ai"

            def is_enabled(self):
                return True

            def get_enabled_models(self):
                return ["test_1"]

            def prompt(self, model, prompt):
                return f"Generated: {prompt}"

        class TestGenerativeAIModelTypePromptError(GenerativeAIModelType):
            type = "test_generative_ai_prompt_error"

            def is_enabled(self):
                return True

            def get_enabled_models(self):
                return ["test_1"]

            def prompt(self, model, prompt):
                raise GenerativeAIPromptError("Test error")

        if (
            TestGenerativeAINoModelType.type
            not in generative_ai_model_type_registry.registry
        ):
            generative_ai_model_type_registry.register(TestGenerativeAINoModelType())

        if (
            TestGenerativeAIModelType.type
            not in generative_ai_model_type_registry.registry
        ):
            generative_ai_model_type_registry.register(TestGenerativeAIModelType())

        if (
            TestGenerativeAIModelTypePromptError.type
            not in generative_ai_model_type_registry.registry
        ):
            generative_ai_model_type_registry.register(
                TestGenerativeAIModelTypePromptError()
            )

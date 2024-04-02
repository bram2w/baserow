from baserow.core.registry import Instance, Registry

from .exceptions import GenerativeAITypeDoesNotExist


class GenerativeAIModelType(Instance):
    def is_enabled(self):
        return False

    def get_enabled_models(self):
        return []

    def prompt(self, model, prompt):
        raise NotImplementedError("The prompt function must be implemented.")


class GenerativeAIModelTypeRegistry(Registry):
    name = "generative_ai_model_type"
    does_not_exist_exception_class = GenerativeAITypeDoesNotExist

    def get_models_per_type(self):
        return {
            key: value.get_enabled_models()
            for key, value in self.registry.items()
            if value.is_enabled()
        }


generative_ai_model_type_registry: GenerativeAIModelTypeRegistry = (
    GenerativeAIModelTypeRegistry()
)

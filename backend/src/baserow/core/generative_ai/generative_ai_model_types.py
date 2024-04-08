from django.conf import settings

from ollama import Client as OllamaClient
from ollama import RequestError as OllamaRequestError
from ollama import ResponseError as OllamaResponseError
from openai import APIStatusError as OpenAIAPIStatusError
from openai import OpenAI, OpenAIError

from baserow.core.generative_ai.exceptions import GenerativeAIPromptError

from .registries import GenerativeAIModelType


class OpenAIGenerativeAIModelType(GenerativeAIModelType):
    type = "openai"

    def get_api_key(self, workspace=None):
        return (
            self.get_workspace_setting(workspace, "api_key")
            or settings.BASEROW_OPENAI_API_KEY
        )

    def get_enabled_models(self, workspace=None):
        workspace_models = self.get_workspace_setting(workspace, "models")
        return workspace_models or settings.BASEROW_OPENAI_MODELS

    def get_organization(self, workspace=None):
        return (
            self.get_workspace_setting(workspace, "organization")
            or settings.BASEROW_OPENAI_ORGANIZATION
        )

    def is_enabled(self, workspace=None):
        api_key = self.get_api_key(workspace)
        return bool(api_key) and bool(self.get_enabled_models(workspace=workspace))

    def get_client(self, workspace=None):
        api_key = self.get_api_key(workspace)
        organization = self.get_organization(workspace)
        return OpenAI(api_key=api_key, organization=organization)

    def prompt(self, model, prompt, workspace=None):
        client = self.get_client(workspace)
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                stream=False,
            )
        except (OpenAIError, OpenAIAPIStatusError) as exc:
            raise GenerativeAIPromptError(str(exc)) from exc
        return chat_completion.choices[0].message.content

    def get_settings_serializer(self):
        from baserow.api.generative_ai.serializers import OpenAISettingsSerializer

        return OpenAISettingsSerializer


class OllamaGenerativeAIModelType(GenerativeAIModelType):
    type = "ollama"

    def get_host(self, workspace=None):
        return (
            self.get_workspace_setting(workspace, "host")
            or settings.BASEROW_OLLAMA_HOST
        )

    def get_enabled_models(self, workspace=None):
        workspace_models = self.get_workspace_setting(workspace, "models")
        return workspace_models or settings.BASEROW_OLLAMA_MODELS

    def is_enabled(self, workspace=None):
        ollama_host = self.get_host(workspace)
        return bool(ollama_host) and bool(self.get_enabled_models(workspace))

    def get_client(self, workspace=None):
        ollama_host = self.get_host(workspace)
        return OllamaClient(host=ollama_host)

    def prompt(self, model, prompt, workspace=None):
        client = self.get_client(workspace)
        try:
            response = client.generate(model=model, prompt=prompt, stream=False)
        except (OllamaRequestError, OllamaResponseError) as exc:
            raise GenerativeAIPromptError(str(exc)) from exc

        return response["response"]

    def get_settings_serializer(self):
        from baserow.api.generative_ai.serializers import OllamaSettingsSerializer

        return OllamaSettingsSerializer

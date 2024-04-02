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

    def is_enabled(self):
        return bool(settings.BASEROW_OPENAI_API_KEY) and bool(self.get_enabled_models())

    def get_enabled_models(self):
        return settings.BASEROW_OPENAI_MODELS

    def prompt(self, model, prompt):
        client = OpenAI(
            api_key=settings.BASEROW_OPENAI_API_KEY,
            organization=settings.BASEROW_OPENAI_ORGANIZATION,
        )
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=model,
                stream=False,
            )
        except (OpenAIError, OpenAIAPIStatusError) as exc:
            raise GenerativeAIPromptError(str(exc)) from exc
        return chat_completion.choices[0].message.content


class OllamaGenerativeAIModelType(GenerativeAIModelType):
    type = "ollama"

    def is_enabled(self):
        return bool(settings.BASEROW_OLLAMA_HOST) and bool(self.get_enabled_models())

    def get_enabled_models(self):
        return settings.BASEROW_OLLAMA_MODELS

    def prompt(self, model, prompt):
        client = OllamaClient(host=settings.BASEROW_OLLAMA_HOST)
        try:
            response = client.generate(model=model, prompt=prompt, stream=False)
        except (OllamaRequestError, OllamaResponseError) as exc:
            raise GenerativeAIPromptError(str(exc)) from exc

        return response["response"]

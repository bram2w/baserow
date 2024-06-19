import os
import re

from django.conf import settings

from ollama import Client as OllamaClient
from ollama import RequestError as OllamaRequestError
from ollama import ResponseError as OllamaResponseError
from openai import APIStatusError as OpenAIAPIStatusError
from openai import OpenAI, OpenAIError

from baserow.core.generative_ai.exceptions import AIFileError, GenerativeAIPromptError
from baserow.core.generative_ai.types import FileId

from .registries import GenerativeAIModelType, GenerativeAIWithFilesModelType


class OpenAIGenerativeAIModelType(
    GenerativeAIWithFilesModelType, GenerativeAIModelType
):
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

    def get_settings_serializer(self):
        from baserow.api.generative_ai.serializers import OpenAISettingsSerializer

        return OpenAISettingsSerializer

    def prompt(self, model, prompt, workspace=None):
        try:
            client = self.get_client(workspace)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                stream=False,
            )
        except (OpenAIError, OpenAIAPIStatusError) as exc:
            raise GenerativeAIPromptError(str(exc)) from exc
        return chat_completion.choices[0].message.content

    def is_file_compatible(self, file_name: str) -> bool:
        # See supported files at:
        # https://platform.openai.com/docs/assistants/tools/file-search/supported-files
        supported_file_extensions = {
            ".doc",
            ".docx",
            ".html",
            ".json",
            ".md",
            ".pdf",
            ".pptx",
            ".txt",
            ".tex",
        }

        _, ext = os.path.splitext(file_name)
        if ext not in supported_file_extensions:
            return False
        return True

    def get_max_file_size(self) -> int:
        return min(512, settings.BASEROW_OPENAI_UPLOADED_FILE_SIZE_LIMIT_MB)

    def upload_file(self, file_name: str, file: bytes, workspace=None) -> FileId:
        try:
            client = self.get_client(workspace=workspace)
            openai_file = client.files.create(
                file=(file_name, file, None), purpose="assistants"
            )
            return openai_file.id
        except (OpenAIError, OpenAIAPIStatusError) as exc:
            raise AIFileError(str(exc)) from exc

    def delete_files(self, file_ids: list[FileId], workspace=None):
        try:
            client = self.get_client(workspace=workspace)
            for file_id in file_ids:
                client.files.delete(file_id)
        except (OpenAIError, OpenAIAPIStatusError) as exc:
            raise AIFileError(str(exc)) from exc

    def prompt_with_files(self, model, prompt, file_ids: list[FileId], workspace=None):
        try:
            client = self.get_client(workspace)
            assistant = client.beta.assistants.create(
                name="Assistant that have access to user files",
                instructions="",
                model=model,
                tools=[{"type": "file_search"}],
            )
            thread = client.beta.threads.create()
            attachments = [
                {"file_id": file_id, "tools": [{"type": "file_search"}]}
                for file_id in file_ids
            ]
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt,
                attachments=attachments,
            )
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
                poll_interval_ms=2000,  # 2 seconds
                timeout=60.0,  # 1 minute
            )
            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                try:
                    message = messages.data[0].content[0].text.value
                except Exception:
                    raise GenerativeAIPromptError(
                        "The OpenAI model didn't respond with an answer."
                    )

                # remove references from the output
                regex = r"【[0-9:]{1,}†source】"
                message = re.sub(regex, "", message, 0)

                return message
            else:
                raise GenerativeAIPromptError(
                    "The OpenAI model didn't respond with an answer."
                )
        except (OpenAIError, OpenAIAPIStatusError) as exc:
            raise GenerativeAIPromptError(str(exc)) from exc
        finally:
            if run and thread:
                if run.status in [
                    "queued",
                    "in_progress",
                    "requires_action",
                    "incomplete",
                ]:
                    client.beta.threads.runs.cancel(run.id, thread_id=thread.id)
            if thread:
                # Deleting the thread should delete all messages within
                client.beta.threads.delete(thread_id=thread.id)
            if assistant:
                client.beta.assistants.delete(assistant_id=assistant.id)


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

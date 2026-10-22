from zipfile import ZipFile

from django.contrib.auth.models import AbstractUser
from django.core.files.storage import Storage
from django.db import transaction
from django.db.transaction import Atomic
from django.urls import URLResolver, include, path

from baserow.contrib.agent.api.serializers import AgentApplicationSerializer
from baserow.contrib.agent.models import AgentApplication
from baserow.contrib.agent.operations import ReadAgentConfigurationOperationType
from baserow.core.ai_provider.constants import AI_PROVIDER_FEATURE_AI_AGENT
from baserow.core.feature_flags import FF_AGENT_BUILDER, feature_flag_is_enabled
from baserow.core.generative_ai.registries import generative_ai_model_type_registry
from baserow.core.handler import CoreHandler
from baserow.core.models import Workspace
from baserow.core.registries import ApplicationType, ImportExportConfig
from baserow.core.storage import ExportZipFile
from baserow.core.utils import ChildProgressBuilder


class AgentApplicationType(ApplicationType):
    type = "agent"
    model_class = AgentApplication
    serializer_field_names = ["name", "readiness"]
    serializer_mixins = [AgentApplicationSerializer]
    request_serializer_field_names = ["name"]
    request_serializer_mixins = []

    def get_api_urls(self) -> list[URLResolver]:
        from baserow.contrib.agent.api import urls as api_urls

        return [path("agent/", include(api_urls, namespace=self.type))]

    def export_safe_transaction_context(self, application: AgentApplication) -> Atomic:
        return transaction.atomic()

    def create_application(
        self,
        user: AbstractUser,
        workspace: Workspace,
        init_with_data: bool = False,
        **kwargs,
    ) -> AgentApplication:
        feature_flag_is_enabled(FF_AGENT_BUILDER, raise_if_disabled=True)
        models = generative_ai_model_type_registry.get_enabled_models_per_type(
            workspace, feature_type=AI_PROVIDER_FEATURE_AI_AGENT
        )
        # Match AI Agent service defaults, only when creating a new application.
        # Reading or importing an Agent must preserve deliberately blank settings.
        if models and not {"provider_type", "model_identifier"}.intersection(kwargs):
            provider_type, identifiers = next(iter(models.items()))
            kwargs.update(provider_type=provider_type, model_identifier=identifiers[0])
        return super().create_application(
            user, workspace, init_with_data=init_with_data, **kwargs
        )

    def export_serialized(
        self,
        application: AgentApplication,
        import_export_config: ImportExportConfig,
        files_zip: ExportZipFile | None = None,
        storage: Storage | None = None,
        progress_builder: ChildProgressBuilder | None = None,
    ) -> dict:
        """Package the configuration, which only configuration readers may export."""

        if import_export_config.exported_by is not None:
            CoreHandler().check_permissions(
                import_export_config.exported_by,
                ReadAgentConfigurationOperationType.type,
                workspace=application.workspace,
                context=application,
            )
        serialized = super().export_serialized(
            application, import_export_config, files_zip, storage, progress_builder
        )
        serialized.update(
            instructions=application.instructions,
            provider_type=application.provider_type,
            model_identifier=application.model_identifier,
        )
        return serialized

    def import_serialized(
        self,
        workspace: Workspace | None,
        serialized_values: dict,
        import_export_config: ImportExportConfig,
        id_mapping: dict,
        files_zip: ZipFile | None = None,
        storage: Storage | None = None,
        progress_builder: ChildProgressBuilder | None = None,
    ) -> AgentApplication:
        """Import the configuration as an independent copy."""

        application = super().import_serialized(
            workspace,
            serialized_values,
            import_export_config,
            id_mapping,
            files_zip,
            storage,
            progress_builder,
        )
        application.instructions = serialized_values.get("instructions", "")
        application.provider_type = serialized_values.get("provider_type") or None
        application.model_identifier = serialized_values.get("model_identifier") or None
        application.save()
        return application

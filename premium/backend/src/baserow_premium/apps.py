from django.apps import AppConfig

from baserow.core.registries import operation_type_registry


class BaserowPremiumConfig(AppConfig):
    name = "baserow_premium"

    def ready(self):
        # noinspection PyUnresolvedReferences
        import baserow_premium.row_comments.recievers  # noqa: F401
        from baserow_premium.api.user.user_data_types import ActiveLicensesDataType
        from baserow_premium.row_comments.row_metadata_types import (
            RowCommentCountMetadataType,
        )

        from baserow.api.user.registries import user_data_registry
        from baserow.contrib.database.export.registries import table_exporter_registry
        from baserow.contrib.database.rows.registries import row_metadata_registry
        from baserow.contrib.database.views.registries import (
            decorator_type_registry,
            decorator_value_provider_type_registry,
            form_view_mode_registry,
            view_ownership_type_registry,
            view_type_registry,
        )
        from baserow.core.action.registries import action_type_registry
        from baserow.core.registries import plugin_registry

        from .export.exporter_types import JSONTableExporter, XMLTableExporter
        from .plugins import PremiumPlugin
        from .views.decorator_types import (
            BackgroundColorDecoratorType,
            LeftBorderColorDecoratorType,
        )
        from .views.decorator_value_provider_types import (
            ConditionalColorValueProviderType,
            SelectColorValueProviderType,
        )
        from .views.form_view_mode_types import FormViewModeTypeSurvey
        from .views.view_types import KanbanViewType

        plugin_registry.register(PremiumPlugin())

        table_exporter_registry.register(JSONTableExporter())
        table_exporter_registry.register(XMLTableExporter())

        row_metadata_registry.register(RowCommentCountMetadataType())

        user_data_registry.register(ActiveLicensesDataType())

        view_type_registry.register(KanbanViewType())

        form_view_mode_registry.register(FormViewModeTypeSurvey())

        decorator_type_registry.register(LeftBorderColorDecoratorType())
        decorator_type_registry.register(BackgroundColorDecoratorType())

        decorator_value_provider_type_registry.register(SelectColorValueProviderType())
        decorator_value_provider_type_registry.register(
            ConditionalColorValueProviderType()
        )

        from .views.view_ownership_types import PersonalViewOwnershipType

        view_ownership_type_registry.register(PersonalViewOwnershipType())

        from baserow_premium.license.license_types import PremiumLicenseType
        from baserow_premium.license.registries import license_type_registry

        license_type_registry.register(PremiumLicenseType())

        from baserow_premium.row_comments.actions import CreateRowCommentActionType

        action_type_registry.register(CreateRowCommentActionType())

        from .row_comments.operations import (
            CreateRowCommentsOperationType,
            ReadRowCommentsOperationType,
        )

        operation_type_registry.register(ReadRowCommentsOperationType())
        operation_type_registry.register(CreateRowCommentsOperationType())

        # The signals must always be imported last because they use the registries
        # which need to be filled first.
        import baserow_premium.views.signals as view_signals  # noqa: F403, F401
        import baserow_premium.ws.signals  # noqa: F403, F401

        view_signals.connect_to_user_pre_delete_signal()

        from baserow.core.registries import permission_manager_type_registry

        from .permission_manager import ViewOwnershipPermissionManagerType

        permission_manager_type_registry.register(ViewOwnershipPermissionManagerType())

from django.apps import AppConfig


class BaserowPremiumConfig(AppConfig):
    name = "baserow_premium"

    def ready(self):
        from baserow.core.registries import plugin_registry
        from baserow.api.user.registries import user_data_registry
        from baserow.contrib.database.export.registries import table_exporter_registry
        from baserow.contrib.database.rows.registries import row_metadata_registry
        from baserow.contrib.database.views.registries import (
            view_type_registry,
            decorator_value_provider_type_registry,
            decorator_type_registry,
        )

        from baserow_premium.row_comments.row_metadata_types import (
            RowCommentCountMetadataType,
        )
        from baserow_premium.api.user.user_data_types import PremiumUserDataType

        # noinspection PyUnresolvedReferences
        import baserow_premium.row_comments.recievers  # noqa: F401

        from .plugins import PremiumPlugin
        from .export.exporter_types import JSONTableExporter, XMLTableExporter
        from .views.view_types import KanbanViewType
        from .views.decorator_value_provider_types import (
            ConditionalColorValueProviderType,
            SelectColorValueProviderType,
        )
        from .views.decorator_types import (
            LeftBorderColorDecoratorType,
            BackgroundColorDecoratorType,
        )

        plugin_registry.register(PremiumPlugin())

        table_exporter_registry.register(JSONTableExporter())
        table_exporter_registry.register(XMLTableExporter())

        row_metadata_registry.register(RowCommentCountMetadataType())

        user_data_registry.register(PremiumUserDataType())

        view_type_registry.register(KanbanViewType())

        decorator_type_registry.register(LeftBorderColorDecoratorType())
        decorator_type_registry.register(BackgroundColorDecoratorType())

        decorator_value_provider_type_registry.register(SelectColorValueProviderType())
        decorator_value_provider_type_registry.register(
            ConditionalColorValueProviderType()
        )

        # The signals must always be imported last because they use the registries
        # which need to be filled first.
        import baserow_premium.ws.signals  # noqa: F403, F401
        import baserow_premium.views.signals  # noqa: F403, F401

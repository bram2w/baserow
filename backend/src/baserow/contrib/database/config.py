from django.apps import AppConfig

from baserow.core.registries import plugin_registry, application_type_registry

from .views.registries import view_type_registry
from .fields.registries import field_type_registry


class DatabaseConfig(AppConfig):
    name = 'baserow.contrib.database'

    def ready(self):
        from .plugins import DatabasePlugin
        plugin_registry.register(DatabasePlugin())

        from .fields.field_types import (
            TextFieldType, LongTextFieldType, NumberFieldType, BooleanFieldType
        )
        field_type_registry.register(TextFieldType())
        field_type_registry.register(LongTextFieldType())
        field_type_registry.register(NumberFieldType())
        field_type_registry.register(BooleanFieldType())

        from .views.view_types import GridViewType
        view_type_registry.register(GridViewType())

        from .application_types import DatabaseApplicationType
        application_type_registry.register(DatabaseApplicationType())

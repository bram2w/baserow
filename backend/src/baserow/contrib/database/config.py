from django.apps import AppConfig

from baserow.core.registries import application_type_registry

from .views.registries import view_type_registry
from .fields.registries import field_type_registry


class DatabaseConfig(AppConfig):
    name = 'baserow.contrib.database'

    def ready(self):
        from .fields.field_types import TextFieldType, NumberFieldType, BooleanFieldType
        field_type_registry.register(TextFieldType())
        field_type_registry.register(NumberFieldType())
        field_type_registry.register(BooleanFieldType())

        from .views.view_types import GridViewType
        view_type_registry.register(GridViewType())

        from .application_types import DatabaseApplicationType
        application_type_registry.register(DatabaseApplicationType())

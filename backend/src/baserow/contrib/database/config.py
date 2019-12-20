from django.apps import AppConfig

from baserow.core.registries import application_type_registry

from .views.registries import view_type_registry


class DatabaseConfig(AppConfig):
    name = 'baserow.contrib.database'

    def ready(self):
        from .application_types import DatabaseApplicationType
        application_type_registry.register(DatabaseApplicationType())

        from .views.view_types import GridViewType
        view_type_registry.register(GridViewType())

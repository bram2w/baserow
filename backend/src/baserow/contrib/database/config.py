from django.apps import AppConfig

from baserow.core.applications import registry


class DatabaseConfig(AppConfig):
    name = 'baserow.contrib.database'

    def ready(self):
        from .applications import DatabaseApplication
        registry.register(DatabaseApplication())

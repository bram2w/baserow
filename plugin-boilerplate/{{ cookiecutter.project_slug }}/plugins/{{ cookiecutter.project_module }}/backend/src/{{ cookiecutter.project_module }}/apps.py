from django.apps import AppConfig

from baserow.core.registries import plugin_registry

from .plugins import PluginNamePlugin


class PluginNameConfig(AppConfig):
    name = '{{ cookiecutter.project_module }}'

    def ready(self):
        plugin_registry.register(PluginNamePlugin())

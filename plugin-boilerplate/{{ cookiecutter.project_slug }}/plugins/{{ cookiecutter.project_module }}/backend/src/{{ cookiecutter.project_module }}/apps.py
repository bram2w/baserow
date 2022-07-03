from baserow.core.registries import plugin_registry
from django.apps import AppConfig


class PluginNameConfig(AppConfig):
    name = "{{ cookiecutter.project_module }}"

    def ready(self):
        from .plugins import PluginNamePlugin

        plugin_registry.register(PluginNamePlugin())

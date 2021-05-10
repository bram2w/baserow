from django.apps import AppConfig


class BaserowPremiumConfig(AppConfig):
    name = "baserow_premium"

    def ready(self):
        from baserow.core.registries import plugin_registry

        from .plugins import PremiumPlugin

        plugin_registry.register(PremiumPlugin())

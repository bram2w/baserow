from baserow.core.registries import Plugin
from django.urls import path, include

from baserow_premium.api import urls as api_urls


class PremiumPlugin(Plugin):
    type = "premium"

    def get_api_urls(self):
        return [
            path("", include(api_urls, namespace=self.type)),
        ]

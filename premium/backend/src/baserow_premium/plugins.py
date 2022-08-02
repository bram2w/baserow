from django.urls import include, path

from baserow_premium.api import urls as api_urls

from baserow.core.registries import Plugin


class PremiumPlugin(Plugin):
    type = "premium"

    def get_api_urls(self):
        return [
            path("", include(api_urls, namespace=self.type)),
        ]

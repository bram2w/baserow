from django.urls import include, path

from baserow_enterprise.api import urls as api_urls

from baserow.core.registries import Plugin


class EnterprisePlugin(Plugin):
    type = "enterprise"

    def get_api_urls(self):
        return [
            path("", include(api_urls, namespace=self.type)),
        ]

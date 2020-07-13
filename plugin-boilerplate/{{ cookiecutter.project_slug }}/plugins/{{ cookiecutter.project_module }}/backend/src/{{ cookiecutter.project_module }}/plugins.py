import logging

from django.urls import path, include

from baserow.core.registries import Plugin

from .api import urls as api_urls


logger = logging.getLogger(__name__)


class PluginNamePlugin(Plugin):
    type = '{{ cookiecutter.project_slug }}'

    def get_api_urls(self):
        return [
            path('{{ cookiecutter.project_slug }}/', include(api_urls, namespace=self.type)),
        ]

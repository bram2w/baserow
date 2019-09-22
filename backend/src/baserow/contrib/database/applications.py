from django.urls import path, include

from baserow.core.applications import Application

from . import api_urls
from .models import Database


class DatabaseApplication(Application):
    type = 'database'
    instance_model = Database

    def get_api_urls(self):
        return [
            path('database/', include(api_urls, namespace=self.type)),
        ]

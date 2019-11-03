from django.urls import path, include

from baserow.core.applications import Application

from . import api_urls
from .models import Database
from .api.v0.serializers import DatabaseSerializer


class DatabaseApplication(Application):
    type = 'database'
    instance_model = Database
    instance_serializer = DatabaseSerializer

    def get_api_urls(self):
        return [
            path('database/', include(api_urls, namespace=self.type)),
        ]

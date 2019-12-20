from django.urls import path, include

from baserow.core.registries import ApplicationType

from .models import Database
from .api.v0 import urls as api_urls
from .api.v0.serializers import DatabaseSerializer


class DatabaseApplicationType(ApplicationType):
    type = 'database'
    model_class = Database
    instance_serializer_class = DatabaseSerializer

    def get_api_v0_urls(self):
        return [
            path('database/', include(api_urls, namespace=self.type)),
        ]

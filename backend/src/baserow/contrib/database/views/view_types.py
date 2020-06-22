from django.urls import path, include

from .registries import ViewType
from .models import GridView


class GridViewType(ViewType):
    type = 'grid'
    model_class = GridView

    def get_api_v0_urls(self):
        from baserow.contrib.database.api.v0.views.grid import urls as api_urls

        return [
            path('grid/', include(api_urls, namespace=self.type)),
        ]

from django.urls import path, include

from .api.v0.tables import urls as table_urls

app_name = 'baserow.contrib.database'

urlpatterns = [
    path('tables/', include(table_urls, namespace='tables')),
]

from django.urls import path, include

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularRedocView

from baserow.core.registries import plugin_registry, application_type_registry

from .user import urls as user_urls
from .groups import urls as group_urls
from .applications import urls as application_urls


app_name = 'baserow.api'

urlpatterns = [
    path('schema.json', SpectacularJSONAPIView.as_view(), name='json_schema'),
    path(
        'redoc/',
        SpectacularRedocView.as_view(url_name='api:json_schema'),
        name='redoc'
    ),
    path('user/', include(user_urls, namespace='user')),
    path('groups/', include(group_urls, namespace='groups')),
    path('applications/', include(application_urls, namespace='applications'))
] + application_type_registry.api_urls + plugin_registry.api_urls

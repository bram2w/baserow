from django.urls import path, include

from baserow.core.applications import registry

from .user import urls as user_urls
from .groups import urls as group_urls
from .applications import urls as application_urls


app_name = 'baserow.api.v0'

urlpatterns = [
    path('user/', include(user_urls, namespace='user')),
    path('groups/', include(group_urls, namespace='groups')),
    path('applications/', include(application_urls, namespace='applications'))
] + registry.api_urls

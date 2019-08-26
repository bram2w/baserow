from django.urls import path, include

from .user import urls as user_urls
from .groups import urls as group_urls


app_name = 'baserow.api.v0'

urlpatterns = [
    path('user/', include(user_urls, namespace='user')),
    path('groups/', include(group_urls, namespace='groups'))
]

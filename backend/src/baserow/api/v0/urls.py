from django.urls import path, include

from .user import urls as user_urls


app_name = 'baserow.api.v0'

urlpatterns = [
    path('user/', include(user_urls, namespace='user'))
]

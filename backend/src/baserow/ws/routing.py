from django.urls import re_path

from .consumers import CoreConsumer


websocket_urlpatterns = [re_path(r"^ws/core/", CoreConsumer.as_asgi())]

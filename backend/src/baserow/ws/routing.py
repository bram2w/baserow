from django.conf.urls import url

from .consumers import CoreConsumer


websocket_urlpatterns = [url(r"^ws/core/", CoreConsumer.as_asgi())]

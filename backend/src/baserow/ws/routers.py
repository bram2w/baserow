from channels.routing import URLRouter

from .auth import JWTTokenAuthMiddleware
from .routing import websocket_urlpatterns


websocket_router = JWTTokenAuthMiddleware(URLRouter(websocket_urlpatterns))

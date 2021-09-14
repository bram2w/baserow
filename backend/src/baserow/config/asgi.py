import django

from channels.routing import ProtocolTypeRouter

from baserow.ws.routers import websocket_router
from django.core.asgi import get_asgi_application


django.setup()

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {"http": django_asgi_app, "websocket": websocket_router}
)

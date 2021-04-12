import django

from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter

from baserow.ws.routers import websocket_router


django.setup()


application = ProtocolTypeRouter({"http": AsgiHandler(), "websocket": websocket_router})

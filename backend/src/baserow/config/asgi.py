from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter

from baserow.core.telemetry.telemetry import setup_logging, setup_telemetry
from baserow.ws.routers import websocket_router

# The telemetry instrumentation library setup needs to run prior to django's setup.
setup_telemetry(add_django_instrumentation=True)

django_asgi_app = get_asgi_application()

# It is critical to setup our own logging after django has been setup and done its own
# logging setup. Otherwise Django will try to destroy and log handlers we added prior.
setup_logging()

application = ProtocolTypeRouter(
    {"http": django_asgi_app, "websocket": websocket_router}
)

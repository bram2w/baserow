from django.urls import include
from django.conf.urls import url
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

from baserow.core.registries import plugin_registry


def health(request):
    return HttpResponse("OK")


urlpatterns = (
    [
        url(r"^api/", include("baserow.api.urls", namespace="api")),
        url(r"^_health$", health, name="health_check"),
    ]
    + plugin_registry.urls
    + static(settings.MEDIA_URL_PATH, document_root=settings.MEDIA_ROOT)
)

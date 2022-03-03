from django.urls import include
from django.urls import re_path, path
from django.conf import settings
from django.conf.urls.static import static
from baserow.core.registries import plugin_registry


urlpatterns = (
    [
        re_path(r"^api/", include("baserow.api.urls", namespace="api")),
        re_path(r"^_health/", include("health_check.urls")),
    ]
    + plugin_registry.urls
    + static(settings.MEDIA_URL_PATH, document_root=settings.MEDIA_ROOT)
)


if settings.DEBUG and "silk" in settings.INSTALLED_APPS:
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]

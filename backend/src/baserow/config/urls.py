from django.urls import include
from django.conf.urls import url
from django.http import HttpResponse

from baserow.core.registries import plugin_registry


def health(request):
    return HttpResponse('OK')


urlpatterns = [
    url(r'^api/v0/', include('baserow.api.v0.urls', namespace='api_v0')),
    url(r'^_health$', health, name='health_check')
] + plugin_registry.urls

from django.urls import include
from django.conf.urls import url


urlpatterns = [
    url(r'^api/v0/', include('baserow.api.v0.urls', namespace='api_v0')),
]

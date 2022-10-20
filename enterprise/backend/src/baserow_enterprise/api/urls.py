from django.urls import include, path

from .role import urls as role_urls
from .teams import urls as teams_urls

app_name = "baserow_enterprise.api"

urlpatterns = [
    path("teams/", include(teams_urls, namespace="teams")),
    path("role/", include(role_urls, namespace="role")),
]

from django.urls import include, path

from .teams import urls as teams_urls

app_name = "baserow_enterprise.api"

urlpatterns = [
    path("teams/", include(teams_urls, namespace="teams")),
]

from django.urls import include, path

from .admin import urls as admin_urls
from .role import urls as role_urls
from .sso import urls as sso_urls
from .teams import urls as teams_urls

app_name = "baserow_enterprise.api"

urlpatterns = [
    path("teams/", include(teams_urls, namespace="teams")),
    path("role/", include(role_urls, namespace="role")),
    path("admin/", include(admin_urls, namespace="admin")),
    path("sso/", include(sso_urls, namespace="sso")),
]

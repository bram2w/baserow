from django.urls import include, path

from .admin import urls as admin_urls
from .sso import urls as sso_urls

app_name = "baserow_enterprise.api"

urlpatterns = [
    path("admin/", include(admin_urls, namespace="admin")),
    path("sso/", include(sso_urls, namespace="sso")),
]

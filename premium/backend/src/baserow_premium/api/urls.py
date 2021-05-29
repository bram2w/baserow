from django.urls import path, include

from .admin import urls as admin_urls

app_name = "baserow_premium.api"

urlpatterns = [
    path("admin/", include(admin_urls, namespace="admin")),
]

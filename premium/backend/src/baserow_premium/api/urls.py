from django.urls import path, include

from .license import urls as license_urls
from .admin import urls as admin_urls
from .row_comments import urls as row_comments_urls


app_name = "baserow_premium.api"

urlpatterns = [
    path("licenses/", include(license_urls, namespace="license")),
    path("admin/", include(admin_urls, namespace="admin")),
    path("row_comments/", include(row_comments_urls, namespace="row_comments")),
]

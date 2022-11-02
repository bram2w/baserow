from django.urls import include, path

from .admin import urls as admin_urls
from .license import urls as license_urls
from .row_comments import urls as row_comments_urls
from .views import urls as view_urls

app_name = "baserow_premium.api"

urlpatterns = [
    path("licenses/", include(license_urls, namespace="license")),
    path("admin/", include(admin_urls, namespace="admin")),
    path("row_comments/", include(row_comments_urls, namespace="row_comments")),
    path("database/view/", include(view_urls, namespace="view")),
]

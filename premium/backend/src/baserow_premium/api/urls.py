from django.urls import path, include

from .user_admin import urls as user_admin_urls
from .admin_dashboard import urls as admin_dashboard_urls


app_name = "baserow_premium.api"

urlpatterns = [
    path("admin/user/", include(user_admin_urls, namespace="admin_user")),
    path(
        "admin/dashboard/", include(admin_dashboard_urls, namespace="admin_dashboard")
    ),
]

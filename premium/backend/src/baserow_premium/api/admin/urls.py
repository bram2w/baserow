from django.urls import path, include

from .users import urls as users_urls
from .groups import urls as groups_urls
from .dashboard import urls as dashboard_urls

app_name = "baserow_premium.api.admin"

urlpatterns = [
    path("dashboard/", include(dashboard_urls, namespace="dashboard")),
    path("users/", include(users_urls, namespace="users")),
    path("groups/", include(groups_urls, namespace="groups")),
]

from django.urls import include, path

from baserow_premium.compat.api.admin import urls as groups_compat_urls

from .dashboard import urls as dashboard_urls
from .users import urls as users_urls
from .workspaces import urls as workspaces_urls

app_name = "baserow_premium.api.admin"

urlpatterns = [
    path("dashboard/", include(dashboard_urls, namespace="dashboard")),
    path("users/", include(users_urls, namespace="users")),
    # GroupDeprecation
    path("groups/", include(groups_compat_urls, namespace="groups")),
    path("workspaces/", include(workspaces_urls, namespace="workspaces")),
]

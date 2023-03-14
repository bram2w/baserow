from django.urls import re_path

from baserow_enterprise.compat.api.role.views import (
    BatchRoleAssignmentsCompatView,
    RoleAssignmentsCompatView,
)

from .views import BatchRoleAssignmentsView, RoleAssignmentsView

app_name = "baserow_enterprise.api.role"

urlpatterns = [
    re_path(
        r"^(?P<workspace_id>[0-9]+)/$",
        RoleAssignmentsView.as_view(),
        name="list",
    ),
    re_path(
        r"^(?P<workspace_id>[0-9]+)/batch/$",
        BatchRoleAssignmentsView.as_view(),
        name="batch",
    ),
]

# GroupDeprecation
urlpatterns += [
    re_path(
        r"^(?P<group_id>[0-9]+)/$",
        RoleAssignmentsCompatView.as_view(),
        name="list",
    ),
    re_path(
        r"^(?P<group_id>[0-9]+)/batch/$",
        BatchRoleAssignmentsCompatView.as_view(),
        name="batch",
    ),
]

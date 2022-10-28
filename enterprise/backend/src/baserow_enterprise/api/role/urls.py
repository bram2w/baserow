from django.urls import re_path

from .views import RoleAssignmentsView

app_name = "baserow_enterprise.api.role"

urlpatterns = [
    re_path(
        r"^(?P<group_id>[0-9]+)/$",
        RoleAssignmentsView.as_view(),
        name="list",
    ),
]

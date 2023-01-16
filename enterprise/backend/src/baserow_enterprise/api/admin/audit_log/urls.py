from django.urls import re_path

from .views import (
    AdminAuditLogActionTypeFilterView,
    AdminAuditLogGroupFilterView,
    AdminAuditLogUserFilterView,
    AdminAuditLogView,
    AsyncAuditLogExportView,
)

app_name = "baserow_enterprise.api.audit_log"

urlpatterns = [
    re_path(r"^$", AdminAuditLogView.as_view(), name="list"),
    re_path(r"users/$", AdminAuditLogUserFilterView.as_view(), name="users"),
    re_path(r"groups/$", AdminAuditLogGroupFilterView.as_view(), name="groups"),
    re_path(
        r"action-types/$",
        AdminAuditLogActionTypeFilterView.as_view(),
        name="action_types",
    ),
    re_path(r"export/$", AsyncAuditLogExportView.as_view(), name="export"),
]

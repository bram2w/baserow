"""
User Permissions API URLs
Ubicación: backend/src/baserow/contrib/database/api/user_permissions/urls.py
"""

from django.urls import re_path

from .views import (
    UserPermissionRulesView,
    UserPermissionRuleView,
    UserPermissionsSummaryView,
    UserFilteredViewView,
    UserPermissionAuditLogView,
)

app_name = "baserow.contrib.database.api.user_permissions"

urlpatterns = [
    # User permission rules endpoints
    re_path(
        r"^table/(?P<table_id>[0-9]+)/$",
        UserPermissionRulesView.as_view(),
        name="list_create"
    ),
    re_path(
        r"^table/(?P<table_id>[0-9]+)/user/(?P<user_id>[0-9]+)/$",
        UserPermissionRuleView.as_view(),
        name="detail"
    ),
    
    # User permissions summary
    re_path(
        r"^table/(?P<table_id>[0-9]+)/user/(?P<user_id>[0-9]+)/summary/$",
        UserPermissionsSummaryView.as_view(),
        name="summary"
    ),
    
    # User filtered views
    re_path(
        r"^table/(?P<table_id>[0-9]+)/filtered-view/$",
        UserFilteredViewView.as_view(),
        name="filtered_view"
    ),
    
    # Audit logs
    re_path(
        r"^table/(?P<table_id>[0-9]+)/audit-logs/$",
        UserPermissionAuditLogView.as_view(),
        name="audit_logs"
    ),
]
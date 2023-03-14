from django.urls import re_path

from .views import WorkspaceUsersView, WorkspaceUserView

app_name = "baserow.api.workspaces.users"

urlpatterns = [
    re_path(
        r"workspace/(?P<workspace_id>[0-9]+)/$",
        WorkspaceUsersView.as_view(),
        name="list",
    ),
    re_path(
        r"(?P<workspace_user_id>[0-9]+)/$", WorkspaceUserView.as_view(), name="item"
    ),
]

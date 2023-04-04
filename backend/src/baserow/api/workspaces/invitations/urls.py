from django.urls import re_path

from .views import (
    AcceptWorkspaceInvitationView,
    RejectWorkspaceInvitationView,
    WorkspaceInvitationByTokenView,
    WorkspaceInvitationsView,
    WorkspaceInvitationView,
)

app_name = "baserow.api.workspaces.invitations"


urlpatterns = [
    re_path(
        r"workspace/(?P<workspace_id>[0-9]+)/$",
        WorkspaceInvitationsView.as_view(),
        name="list",
    ),
    re_path(
        r"token/(?P<token>.*)/$", WorkspaceInvitationByTokenView.as_view(), name="token"
    ),
    re_path(
        r"(?P<workspace_invitation_id>[0-9]+)/$",
        WorkspaceInvitationView.as_view(),
        name="item",
    ),
    re_path(
        r"(?P<workspace_invitation_id>[0-9]+)/accept/$",
        AcceptWorkspaceInvitationView.as_view(),
        name="accept",
    ),
    re_path(
        r"(?P<workspace_invitation_id>[0-9]+)/reject/$",
        RejectWorkspaceInvitationView.as_view(),
        name="reject",
    ),
]

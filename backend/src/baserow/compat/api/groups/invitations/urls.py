from django.urls import re_path

from baserow.compat.api.groups.invitations.views import (
    AcceptGroupInvitationCompatView,
    GroupInvitationByTokenCompatView,
    GroupInvitationCompatView,
    GroupInvitationsCompatView,
    RejectGroupInvitationCompatView,
)

app_name = "baserow.api.groups.invitations"

urlpatterns = [
    re_path(
        r"group/(?P<group_id>[0-9]+)/$",
        GroupInvitationsCompatView.as_view(),
        name="list",
    ),
    re_path(
        r"token/(?P<token>.*)/$",
        GroupInvitationByTokenCompatView.as_view(),
        name="token",
    ),
    re_path(
        r"(?P<group_invitation_id>[0-9]+)/$",
        GroupInvitationCompatView.as_view(),
        name="item",
    ),
    re_path(
        r"(?P<group_invitation_id>[0-9]+)/accept/$",
        AcceptGroupInvitationCompatView.as_view(),
        name="accept",
    ),
    re_path(
        r"(?P<group_invitation_id>[0-9]+)/reject/$",
        RejectGroupInvitationCompatView.as_view(),
        name="reject",
    ),
]

from django.urls import re_path

from .views import (
    GroupInvitationsView,
    GroupInvitationView,
    AcceptGroupInvitationView,
    RejectGroupInvitationView,
    GroupInvitationByTokenView,
)


app_name = "baserow.api.groups.invitations"


urlpatterns = [
    re_path(
        r"group/(?P<group_id>[0-9]+)/$", GroupInvitationsView.as_view(), name="list"
    ),
    re_path(
        r"token/(?P<token>.*)/$", GroupInvitationByTokenView.as_view(), name="token"
    ),
    re_path(
        r"(?P<group_invitation_id>[0-9]+)/$", GroupInvitationView.as_view(), name="item"
    ),
    re_path(
        r"(?P<group_invitation_id>[0-9]+)/accept/$",
        AcceptGroupInvitationView.as_view(),
        name="accept",
    ),
    re_path(
        r"(?P<group_invitation_id>[0-9]+)/reject/$",
        RejectGroupInvitationView.as_view(),
        name="reject",
    ),
]

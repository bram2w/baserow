from django.conf.urls import url

from .views import (
    GroupInvitationsView,
    GroupInvitationView,
    AcceptGroupInvitationView,
    RejectGroupInvitationView,
    GroupInvitationByTokenView,
)


app_name = "baserow.api.groups.invitations"


urlpatterns = [
    url(r"group/(?P<group_id>[0-9]+)/$", GroupInvitationsView.as_view(), name="list"),
    url(r"token/(?P<token>.*)/$", GroupInvitationByTokenView.as_view(), name="token"),
    url(
        r"(?P<group_invitation_id>[0-9]+)/$", GroupInvitationView.as_view(), name="item"
    ),
    url(
        r"(?P<group_invitation_id>[0-9]+)/accept/$",
        AcceptGroupInvitationView.as_view(),
        name="accept",
    ),
    url(
        r"(?P<group_invitation_id>[0-9]+)/reject/$",
        RejectGroupInvitationView.as_view(),
        name="reject",
    ),
]

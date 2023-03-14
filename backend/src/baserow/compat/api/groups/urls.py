from django.urls import include, path, re_path

from baserow.compat.api.groups.invitations import urls as invitation_compat_urls
from baserow.compat.api.groups.views import (
    GroupCompatView,
    GroupLeaveCompatView,
    GroupOrderCompatView,
    GroupPermissionsCompatView,
    GroupsCompatView,
)
from baserow.compat.api.users import urls as user_compat_urls

app_name = "baserow.api.groups"

urlpatterns = [
    path("users/", include(user_compat_urls, namespace="users")),
    path("invitations/", include(invitation_compat_urls, namespace="invitations")),
    re_path(r"^$", GroupsCompatView.as_view(), name="list"),
    re_path(
        r"(?P<group_id>[0-9]+)/permissions/$",
        GroupPermissionsCompatView.as_view(),
        name="permissions",
    ),
    re_path(
        r"(?P<group_id>[0-9]+)/leave/$", GroupLeaveCompatView.as_view(), name="leave"
    ),
    re_path(r"(?P<group_id>[0-9]+)/$", GroupCompatView.as_view(), name="item"),
    re_path(r"order/$", GroupOrderCompatView.as_view(), name="order"),
]

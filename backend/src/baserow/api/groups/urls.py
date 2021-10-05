from django.urls import re_path
from django.urls import path, include

from .views import GroupsView, GroupView, GroupLeaveView, GroupOrderView
from .users import urls as user_urls
from .invitations import urls as invitation_urls


app_name = "baserow.api.groups"

urlpatterns = [
    path("users/", include(user_urls, namespace="users")),
    path("invitations/", include(invitation_urls, namespace="invitations")),
    re_path(r"^$", GroupsView.as_view(), name="list"),
    re_path(r"(?P<group_id>[0-9]+)/leave/$", GroupLeaveView.as_view(), name="leave"),
    re_path(r"(?P<group_id>[0-9]+)/$", GroupView.as_view(), name="item"),
    re_path(r"order/$", GroupOrderView.as_view(), name="order"),
]

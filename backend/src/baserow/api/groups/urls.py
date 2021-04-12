from django.conf.urls import url
from django.urls import path, include

from .views import GroupsView, GroupView, GroupOrderView
from .users import urls as user_urls
from .invitations import urls as invitation_urls


app_name = "baserow.api.groups"

urlpatterns = [
    path("users/", include(user_urls, namespace="users")),
    path("invitations/", include(invitation_urls, namespace="invitations")),
    url(r"^$", GroupsView.as_view(), name="list"),
    url(r"(?P<group_id>[0-9]+)/$", GroupView.as_view(), name="item"),
    url(r"order/$", GroupOrderView.as_view(), name="order"),
]

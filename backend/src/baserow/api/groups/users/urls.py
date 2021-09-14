from django.urls import re_path

from .views import GroupUsersView, GroupUserView


app_name = "baserow.api.groups.users"

urlpatterns = [
    re_path(r"group/(?P<group_id>[0-9]+)/$", GroupUsersView.as_view(), name="list"),
    re_path(r"(?P<group_user_id>[0-9]+)/$", GroupUserView.as_view(), name="item"),
]

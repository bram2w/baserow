from django.urls import re_path

from baserow_premium.api.admin.groups.views import GroupsAdminView, GroupAdminView


app_name = "baserow_premium.api.admin.groups"

urlpatterns = [
    re_path(r"^$", GroupsAdminView.as_view(), name="list"),
    re_path(r"^(?P<group_id>[0-9]+)/$", GroupAdminView.as_view(), name="edit"),
]

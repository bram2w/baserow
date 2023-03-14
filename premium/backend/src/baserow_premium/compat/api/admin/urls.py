from django.urls import re_path

from baserow_premium.compat.api.admin.groups.views import (
    GroupAdminCompatView,
    GroupsAdminCompatView,
)

app_name = "baserow_premium.api.admin.groups"

urlpatterns = [
    re_path(r"^$", GroupsAdminCompatView.as_view(), name="list"),
    re_path(r"^(?P<group_id>[0-9]+)/$", GroupAdminCompatView.as_view(), name="edit"),
]

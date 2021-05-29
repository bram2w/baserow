from django.conf.urls import url

from baserow_premium.api.admin.groups.views import GroupsAdminView, GroupAdminView


app_name = "baserow_premium.api.admin.groups"

urlpatterns = [
    url(r"^$", GroupsAdminView.as_view(), name="list"),
    url(r"^(?P<group_id>[0-9]+)/$", GroupAdminView.as_view(), name="edit"),
]

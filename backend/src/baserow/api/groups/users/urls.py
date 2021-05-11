from django.conf.urls import url

from .views import GroupUsersView, GroupUserView


app_name = "baserow.api.groups.users"

urlpatterns = [
    url(r"group/(?P<group_id>[0-9]+)/$", GroupUsersView.as_view(), name="list"),
    url(r"(?P<group_user_id>[0-9]+)/$", GroupUserView.as_view(), name="item"),
]

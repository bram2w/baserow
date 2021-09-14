from django.urls import re_path

from baserow_premium.api.admin.users.views import UsersAdminView, UserAdminView


app_name = "baserow_premium.api.admin.users"

urlpatterns = [
    re_path(r"^$", UsersAdminView.as_view(), name="list"),
    re_path(r"^(?P<user_id>[0-9]+)/$", UserAdminView.as_view(), name="edit"),
]

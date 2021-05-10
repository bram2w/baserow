from django.conf.urls import url

from baserow_premium.api.user_admin.views import UsersAdminView, UserAdminView


app_name = "baserow_premium.api.user_admin"

urlpatterns = [
    url(r"^$", UsersAdminView.as_view(), name="users"),
    url(r"^(?P<user_id>[0-9]+)/$", UserAdminView.as_view(), name="user_edit"),
]

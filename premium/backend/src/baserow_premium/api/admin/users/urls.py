from django.conf.urls import url

from baserow_premium.api.admin.users.views import UsersAdminView, UserAdminView


app_name = "baserow_premium.api.admin.users"

urlpatterns = [
    url(r"^$", UsersAdminView.as_view(), name="list"),
    url(r"^(?P<user_id>[0-9]+)/$", UserAdminView.as_view(), name="edit"),
]

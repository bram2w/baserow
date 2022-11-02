from django.urls import re_path

from .views import (
    AdminAuthProvidersView,
    AdminAuthProviderView,
    AdminNextAuthProviderIdView,
)

app_name = "baserow_enterprise.api.sso"

urlpatterns = [
    re_path(r"^$", AdminAuthProvidersView.as_view(), name="list"),
    re_path(
        r"(?P<auth_provider_id>[0-9]+)/$", AdminAuthProviderView.as_view(), name="item"
    ),
    re_path(r"^next-id/$", AdminNextAuthProviderIdView.as_view(), name="next_id"),
]

from django.urls import re_path

from .views import (
    AdminCheckLicense,
    AdminLicenseFillSeatsView,
    AdminLicenseLookupUsersView,
    AdminLicensesView,
    AdminLicenseUserView,
    AdminLicenseView,
    AdminRemoveAllUsersFromLicenseView,
)

app_name = "baserow_premium.api.license"

urlpatterns = [
    re_path(r"^$", AdminLicensesView.as_view(), name="list"),
    re_path(r"^(?P<id>[0-9]+)/$", AdminLicenseView.as_view(), name="item"),
    re_path(
        r"^(?P<id>[0-9]+)/lookup-users/$",
        AdminLicenseLookupUsersView.as_view(),
        name="lookup_users",
    ),
    re_path(
        r"^(?P<id>[0-9]+)/fill-seats/$",
        AdminLicenseFillSeatsView.as_view(),
        name="fill_seats",
    ),
    re_path(
        r"^(?P<id>[0-9]+)/remove-all-users/$",
        AdminRemoveAllUsersFromLicenseView.as_view(),
        name="remove_all_users",
    ),
    re_path(
        r"^(?P<id>[0-9]+)/check/$",
        AdminCheckLicense.as_view(),
        name="check",
    ),
    re_path(
        r"^(?P<id>[0-9]+)/(?P<user_id>[0-9]+)/$",
        AdminLicenseUserView.as_view(),
        name="user",
    ),
]

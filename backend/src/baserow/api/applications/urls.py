from django.urls import re_path

from .views import (
    ApplicationsView,
    AllApplicationsView,
    ApplicationView,
    OrderApplicationsView,
)


app_name = "baserow.api.group"


urlpatterns = [
    re_path(r"group/(?P<group_id>[0-9]+)/$", ApplicationsView.as_view(), name="list"),
    re_path(
        r"group/(?P<group_id>[0-9]+)/order/$",
        OrderApplicationsView.as_view(),
        name="order",
    ),
    re_path(r"(?P<application_id>[0-9]+)/$", ApplicationView.as_view(), name="item"),
    re_path(r"$", AllApplicationsView.as_view(), name="list"),
]

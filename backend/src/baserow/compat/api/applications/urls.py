from django.urls import re_path

from baserow.compat.api.applications.views import (
    ApplicationsCompatView,
    OrderApplicationsCompatView,
)

app_name = "baserow.api.group"

urlpatterns = [
    re_path(
        r"group/(?P<group_id>[0-9]+)/$",
        ApplicationsCompatView.as_view(),
        name="list",
    ),
    re_path(
        r"group/(?P<group_id>[0-9]+)/order/$",
        OrderApplicationsCompatView.as_view(),
        name="order",
    ),
]

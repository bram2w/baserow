from django.urls import re_path

from .views import (
    AllApplicationsView,
    ApplicationsView,
    ApplicationView,
    AsyncDuplicateApplicationView,
    OrderApplicationsView,
)

app_name = "baserow.api.workspace"


urlpatterns = [
    re_path(
        r"workspace/(?P<workspace_id>[0-9]+)/$", ApplicationsView.as_view(), name="list"
    ),
    re_path(
        r"workspace/(?P<workspace_id>[0-9]+)/order/$",
        OrderApplicationsView.as_view(),
        name="order",
    ),
    re_path(r"(?P<application_id>[0-9]+)/$", ApplicationView.as_view(), name="item"),
    re_path(
        r"(?P<application_id>[0-9]+)/duplicate/async/$",
        AsyncDuplicateApplicationView.as_view(),
        name="async_duplicate",
    ),
    re_path(r"$", AllApplicationsView.as_view(), name="list"),
]

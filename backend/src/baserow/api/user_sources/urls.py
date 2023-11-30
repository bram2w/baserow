from django.urls import re_path

from baserow.api.user_sources.views import (
    MoveUserSourceView,
    UserSourcesView,
    UserSourceView,
)

app_name = "baserow.api.user_sources"

urlpatterns = [
    re_path(
        r"application/(?P<application_id>[0-9]+)/user_sources/$",
        UserSourcesView.as_view(),
        name="list",
    ),
    re_path(
        r"user_source/(?P<user_source_id>[0-9]+)/$",
        UserSourceView.as_view(),
        name="item",
    ),
    re_path(
        r"user_source/(?P<user_source_id>[0-9]+)/move/$",
        MoveUserSourceView.as_view(),
        name="move",
    ),
]

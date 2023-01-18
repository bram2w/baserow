from django.urls import re_path

from .views import RestoreSnapshotView, SnapshotsView, SnapshotView

app_name = "baserow.api.snapshot"


urlpatterns = [
    re_path(
        r"^application/(?P<application_id>[0-9]+)/$",
        SnapshotsView.as_view(),
        name="list",
    ),
    re_path(
        r"(?P<snapshot_id>[0-9]+)/$",
        SnapshotView.as_view(),
        name="item",
    ),
    re_path(
        r"(?P<snapshot_id>[0-9]+)/restore/$",
        RestoreSnapshotView.as_view(),
        name="restore",
    ),
]

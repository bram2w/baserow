from django.urls import re_path

from baserow.compat.api.trash.views import TrashContentsCompatView

app_name = "baserow.api.trash"

urlpatterns = [
    re_path(
        r"^group/(?P<group_id>[0-9]+)/$",
        TrashContentsCompatView.as_view(),
        name="contents",
    ),
]

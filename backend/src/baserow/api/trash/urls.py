from django.urls import re_path

from .views import TrashContentsView, TrashStructureView, TrashItemView

app_name = "baserow.api.trash"

urlpatterns = [
    re_path(r"^$", TrashStructureView.as_view(), name="list"),
    re_path(
        r"^group/(?P<group_id>[0-9]+)/$",
        TrashContentsView.as_view(),
        name="contents",
    ),
    re_path(
        r"^restore/$",
        TrashItemView.as_view(),
        name="restore",
    ),
]

from django.conf.urls import url

from .views import TrashContentsView, TrashStructureView, TrashItemView

app_name = "baserow.api.trash"

urlpatterns = [
    url(r"^$", TrashStructureView.as_view(), name="list"),
    url(
        r"^group/(?P<group_id>[0-9]+)/$",
        TrashContentsView.as_view(),
        name="contents",
    ),
    url(
        r"^restore/$",
        TrashItemView.as_view(),
        name="restore",
    ),
]

from django.urls import re_path

from baserow.contrib.builder.api.elements.views import (
    DuplicateElementView,
    ElementsView,
    ElementView,
    MoveElementView,
)

app_name = "baserow.contrib.builder.api.elements"

urlpatterns = [
    re_path(
        r"page/(?P<page_id>[0-9]+)/elements/$",
        ElementsView.as_view(),
        name="list",
    ),
    re_path(r"element/(?P<element_id>[0-9]+)/$", ElementView.as_view(), name="item"),
    re_path(
        r"element/(?P<element_id>[0-9]+)/move/$", MoveElementView.as_view(), name="move"
    ),
    re_path(
        r"element/(?P<element_id>[0-9]+)/duplicate/$",
        DuplicateElementView.as_view(),
        name="duplicate",
    ),
]

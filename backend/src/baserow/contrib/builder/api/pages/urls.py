from django.urls import re_path

from baserow.contrib.builder.api.pages.views import (
    AsyncDuplicatePageView,
    OrderPagesView,
    PagesView,
    PageView,
)

app_name = "baserow.contrib.builder.api.pages"

urlpatterns_with_builder_id = [
    re_path(
        r"$",
        PagesView.as_view(),
        name="list",
    ),
    re_path(r"order/$", OrderPagesView.as_view(), name="order"),
]

urlpatterns_without_builder_id = [
    re_path(r"(?P<page_id>[0-9]+)/$", PageView.as_view(), name="item"),
    re_path(
        r"(?P<page_id>[0-9]+)/duplicate/async/$",
        AsyncDuplicatePageView.as_view(),
        name="async_duplicate",
    ),
]

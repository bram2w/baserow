from django.urls import re_path

from baserow.contrib.builder.api.elements.views import (
    ElementsView,
    ElementView,
    OrderElementsPageView,
)

app_name = "baserow.contrib.builder.api.elements"

urlpatterns = [
    re_path(
        r"page/(?P<page_id>[0-9]+)/elements/$",
        ElementsView.as_view(),
        name="list",
    ),
    re_path(
        r"page/(?P<page_id>[0-9]+)/elements/order/$",
        OrderElementsPageView.as_view(),
        name="order",
    ),
    re_path(r"element/(?P<element_id>[0-9]+)/$", ElementView.as_view(), name="item"),
]

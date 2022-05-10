from django.urls import re_path

from .views import (
    GridViewView,
    PublicGridViewInfoView,
    PublicGridViewRowsView,
    GridViewFieldAggregationView,
    GridViewFieldAggregationsView,
)

app_name = "baserow.contrib.database.api.views.grid"

urlpatterns = [
    re_path(
        r"(?P<view_id>[0-9]+)/aggregation/(?P<field_id>[0-9]+)/$",
        GridViewFieldAggregationView.as_view(),
        name="field-aggregation",
    ),
    re_path(
        r"(?P<view_id>[0-9]+)/aggregations/$",
        GridViewFieldAggregationsView.as_view(),
        name="field-aggregations",
    ),
    re_path(r"(?P<view_id>[0-9]+)/$", GridViewView.as_view(), name="list"),
    re_path(
        r"(?P<slug>[-\w]+)/public/info/$",
        PublicGridViewInfoView.as_view(),
        name="public_info",
    ),
    re_path(
        r"(?P<slug>[-\w]+)/public/rows/$",
        PublicGridViewRowsView.as_view(),
        name="public_rows",
    ),
]

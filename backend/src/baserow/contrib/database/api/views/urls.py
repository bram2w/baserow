from django.urls import re_path

from baserow.contrib.database.views.registries import view_type_registry

from .views import (
    ViewsView,
    ViewView,
    OrderViewsView,
    ViewFiltersView,
    ViewFilterView,
    ViewSortingsView,
    ViewSortView,
    ViewFieldOptionsView,
)


app_name = "baserow.contrib.database.api.views"

urlpatterns = view_type_registry.api_urls + [
    re_path(r"table/(?P<table_id>[0-9]+)/$", ViewsView.as_view(), name="list"),
    re_path(
        r"table/(?P<table_id>[0-9]+)/order/$", OrderViewsView.as_view(), name="order"
    ),
    re_path(
        r"filter/(?P<view_filter_id>[0-9]+)/$",
        ViewFilterView.as_view(),
        name="filter_item",
    ),
    re_path(
        r"sort/(?P<view_sort_id>[0-9]+)/$", ViewSortView.as_view(), name="sort_item"
    ),
    re_path(r"(?P<view_id>[0-9]+)/$", ViewView.as_view(), name="item"),
    re_path(
        r"(?P<view_id>[0-9]+)/filters/$", ViewFiltersView.as_view(), name="list_filters"
    ),
    re_path(
        r"(?P<view_id>[0-9]+)/sortings/$",
        ViewSortingsView.as_view(),
        name="list_sortings",
    ),
    re_path(
        r"(?P<view_id>[0-9]+)/field-options/$",
        ViewFieldOptionsView.as_view(),
        name="field_options",
    ),
]

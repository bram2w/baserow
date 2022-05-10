from django.urls import re_path

from baserow.contrib.database.fields.registries import field_type_registry

from .views import FieldsView, FieldView, UniqueRowValueFieldView


app_name = "baserow.contrib.database.api.fields"

urlpatterns = field_type_registry.api_urls + [
    re_path(r"table/(?P<table_id>[0-9]+)/$", FieldsView.as_view(), name="list"),
    re_path(
        r"(?P<field_id>[0-9]+)/unique_row_values/$",
        UniqueRowValueFieldView.as_view(),
        name="unique_row_values",
    ),
    re_path(r"(?P<field_id>[0-9]+)/$", FieldView.as_view(), name="item"),
]

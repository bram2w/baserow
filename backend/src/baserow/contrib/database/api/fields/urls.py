from django.conf.urls import url

from baserow.contrib.database.fields.registries import field_type_registry

from .views import FieldsView, FieldView


app_name = "baserow.contrib.database.api.fields"

urlpatterns = field_type_registry.api_urls + [
    url(r"table/(?P<table_id>[0-9]+)/$", FieldsView.as_view(), name="list"),
    url(r"(?P<field_id>[0-9]+)/$", FieldView.as_view(), name="item"),
]

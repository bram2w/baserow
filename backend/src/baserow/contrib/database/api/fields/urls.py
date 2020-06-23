from django.conf.urls import url

from .views import FieldsView, FieldView


app_name = 'baserow.contrib.database.api.fields'

urlpatterns = [
    url(r'table/(?P<table_id>[0-9]+)/$', FieldsView.as_view(), name='list'),
    url(r'(?P<field_id>[0-9]+)/$', FieldView.as_view(), name='item'),
]

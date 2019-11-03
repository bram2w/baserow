from django.conf.urls import url

from .views import TablesView, TableView


app_name = 'baserow.contrib.api.v0.tables'

urlpatterns = [
    url(r'database/(?P<database_id>[0-9]+)/$', TablesView.as_view(), name='list'),
    url(r'(?P<table_id>[0-9]+)/$', TableView.as_view(), name='item'),
]

from django.urls import re_path

from .views import TablesView, TableView, OrderTablesView


app_name = "baserow.contrib.database.api.tables"

urlpatterns = [
    re_path(r"database/(?P<database_id>[0-9]+)/$", TablesView.as_view(), name="list"),
    re_path(
        r"database/(?P<database_id>[0-9]+)/order/$",
        OrderTablesView.as_view(),
        name="order",
    ),
    re_path(r"(?P<table_id>[0-9]+)/$", TableView.as_view(), name="item"),
]

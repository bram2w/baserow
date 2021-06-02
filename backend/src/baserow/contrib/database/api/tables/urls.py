from django.conf.urls import url

from .views import TablesView, TableView, OrderTablesView


app_name = "baserow.contrib.database.api.tables"

urlpatterns = [
    url(r"database/(?P<database_id>[0-9]+)/$", TablesView.as_view(), name="list"),
    url(
        r"database/(?P<database_id>[0-9]+)/order/$",
        OrderTablesView.as_view(),
        name="order",
    ),
    url(r"(?P<table_id>[0-9]+)/$", TableView.as_view(), name="item"),
]

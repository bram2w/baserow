from django.conf.urls import url

from .views import ExportJobView, ExportTableView


app_name = "baserow.contrib.database.api.export"

urlpatterns = [
    url(
        r"table/(?P<table_id>[0-9]+)/$",
        ExportTableView.as_view(),
        name="export_table",
    ),
    url(r"(?P<job_id>[0-9]+)/$", ExportJobView.as_view(), name="get"),
]

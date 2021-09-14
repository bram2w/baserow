from django.urls import re_path

from .views import ExportJobView, ExportTableView


app_name = "baserow.contrib.database.api.export"

urlpatterns = [
    re_path(
        r"table/(?P<table_id>[0-9]+)/$",
        ExportTableView.as_view(),
        name="export_table",
    ),
    re_path(r"(?P<job_id>[0-9]+)/$", ExportJobView.as_view(), name="get"),
]

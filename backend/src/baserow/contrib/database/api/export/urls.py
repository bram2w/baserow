from django.conf.urls import url

from baserow.contrib.database.views.registries import view_type_registry
from .views import ExportJobView, ExportTableView

app_name = "baserow.contrib.database.api.export"

urlpatterns = view_type_registry.api_urls + [
    url(
        r"table/(?P<table_id>[0-9]+)/$",
        ExportTableView.as_view(),
        name="export_table",
    ),
    url(r"(?P<job_id>[0-9]+)/$", ExportJobView.as_view(), name="get"),
]

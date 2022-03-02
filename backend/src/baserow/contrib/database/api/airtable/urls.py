from django.urls import re_path

from baserow.contrib.database.api.airtable.views import (
    CreateAirtableImportJobView,
    AirtableImportJobView,
)


app_name = "baserow.api.airtable"

urlpatterns = [
    re_path(
        r"import-job/(?P<job_id>[0-9]+)/$", AirtableImportJobView.as_view(), name="item"
    ),
    re_path(
        r"create-import-job/$", CreateAirtableImportJobView.as_view(), name="create"
    ),
]

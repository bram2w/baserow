from django.db import models

from baserow.core.jobs.models import Job
from baserow.contrib.database.table.models import Table


def file_import_directory_path(instance, filename):
    return f"user_{instance.user.id}/file_import/job__{instance.id}.json"


class FileImportJob(Job):
    table = models.ForeignKey(
        Table, on_delete=models.SET_NULL, null=True, related_name="import_jobs"
    )
    data_file = models.FileField(upload_to=file_import_directory_path, null=True)
    report = models.JSONField(default=lambda: {"failing_rows": {}})

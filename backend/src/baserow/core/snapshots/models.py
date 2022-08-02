from django.db import models

from baserow.core.jobs.models import Job
from baserow.core.models import Snapshot


class CreateSnapshotJob(Job):
    snapshot: Snapshot = models.ForeignKey(
        Snapshot, null=True, on_delete=models.SET_NULL
    )


class RestoreSnapshotJob(Job):
    snapshot: Snapshot = models.ForeignKey(
        Snapshot, null=True, on_delete=models.SET_NULL
    )

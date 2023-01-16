from django.db import models

from baserow.core.jobs.mixins import JobWithUserIpAddress
from baserow.core.jobs.models import Job
from baserow.core.models import Snapshot


class CreateSnapshotJob(JobWithUserIpAddress, Job):
    snapshot: Snapshot = models.ForeignKey(
        Snapshot, null=True, on_delete=models.SET_NULL
    )


class RestoreSnapshotJob(JobWithUserIpAddress, Job):
    snapshot: Snapshot = models.ForeignKey(
        Snapshot, null=True, on_delete=models.SET_NULL
    )

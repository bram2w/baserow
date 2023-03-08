from django.db import models

from baserow.core.jobs.mixins import JobWithUserIpAddress
from baserow.core.jobs.models import Job
from baserow.core.models import Application, Group


class AirtableImportJob(JobWithUserIpAddress, Job):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        help_text="The group where the Airtable base must be imported into.",
    )
    airtable_share_id = models.CharField(
        max_length=18,
        help_text="Public ID of the shared Airtable base that must be imported.",
    )
    database = models.ForeignKey(
        Application,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The imported Baserow database.",
    )

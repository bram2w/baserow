from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.cache import cache

from baserow.core.models import Group
from baserow.core.mixins import CreatedAndUpdatedOnMixin
from baserow.core.models import Application

from .constants import (
    AIRTABLE_EXPORT_JOB_DOWNLOADING_PENDING,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED,
)
from .cache import airtable_import_job_progress_key

User = get_user_model()


class AirtableImportJobQuerySet(models.QuerySet):
    def is_running(self):
        return self.filter(
            ~Q(state=AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED),
            ~Q(state=AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED),
        )


class AirtableImportJob(CreatedAndUpdatedOnMixin, models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="The user that has created the job"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        help_text="The group where the Airtable base must be imported into.",
    )
    airtable_share_id = models.CharField(
        max_length=18,
        help_text="Public ID of the shared Airtable base that must be imported.",
    )
    timezone = models.CharField(null=True, max_length=255)
    progress_percentage = models.IntegerField(
        default=0,
        help_text="A percentage indicating how far along the import job is. 100 means "
        "that it's finished.",
    )
    state = models.CharField(
        max_length=128,
        default=AIRTABLE_EXPORT_JOB_DOWNLOADING_PENDING,
        help_text="Indicates the state of the import job.",
    )
    error = models.TextField(
        blank=True, default="", help_text="An error message if something went wrong."
    )
    human_readable_error = models.TextField(
        blank=True,
        default="",
        help_text="A human readable error message indicating what went wrong.",
    )
    database = models.ForeignKey(
        Application,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The imported Baserow database.",
    )

    objects = AirtableImportJobQuerySet.as_manager()

    def get_from_cached_value_or_from_self(self, name: str) -> any:
        """
        Because the `progress_percentage` and `state` are updated via a transaction,
        we also temporarily store the progress in the Redis cache. This is needed
        because other database connection, for example a gunicorn worker, can't get
        the latest progress from the PostgreSQL table because it's updated in a
        transaction.

        This method tries to get the progress from the cache and if it's not found,
        it falls back on the job table entry data.

        :param name: The name in the cache entry dict.
        :return: The correct value.
        """

        return cache.get(airtable_import_job_progress_key(self.id), default={}).get(
            name, getattr(self, name)
        )

    def get_cached_progress_percentage(self) -> int:
        return self.get_from_cached_value_or_from_self("progress_percentage")

    def get_cached_state(self) -> str:
        return self.get_from_cached_value_or_from_self("state")

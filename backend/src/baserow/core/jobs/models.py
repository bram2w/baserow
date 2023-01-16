from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models

from baserow.core.mixins import CreatedAndUpdatedOnMixin, PolymorphicContentTypeMixin

from .cache import job_progress_key
from .constants import JOB_FAILED, JOB_FINISHED, JOB_PENDING

User = get_user_model()


def get_default_job_content_type():
    return ContentType.objects.get_for_model(Job)


class JobQuerySet(models.QuerySet):
    def is_running(self):
        return self.exclude(state__in=[JOB_PENDING, JOB_FINISHED, JOB_FAILED])

    def is_finished(self):
        return self.filter(state__in=[JOB_FINISHED, JOB_FAILED])

    def is_pending_or_running(self):
        return self.exclude(state__in=[JOB_FINISHED, JOB_FAILED])


class Job(CreatedAndUpdatedOnMixin, PolymorphicContentTypeMixin, models.Model):
    content_type = models.ForeignKey(
        ContentType,
        verbose_name="content type",
        related_name="database_jobs",
        on_delete=models.SET(get_default_job_content_type),
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="The user that has created the job"
    )
    progress_percentage = models.IntegerField(
        default=0,
        help_text="A percentage indicating how far along the job is. 100 means "
        "that it's finished.",
    )
    state = models.CharField(
        db_index=True,
        max_length=128,
        default=JOB_PENDING,
        help_text="Indicates the state of the job.",
    )
    error = models.TextField(
        blank=True, default="", help_text="An error message if something went wrong."
    )
    human_readable_error = models.TextField(
        blank=True,
        default="",
        help_text="A human readable error message indicating what went wrong.",
    )

    objects = JobQuerySet.as_manager()

    def get_from_cached_value_or_from_self(self, name: str) -> Any:
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

        return cache.get(job_progress_key(self.id), default={}).get(
            name, getattr(self, name)
        )

    def get_cached_progress_percentage(self) -> int:
        return self.get_from_cached_value_or_from_self("progress_percentage")

    def get_cached_state(self) -> str:
        return self.get_from_cached_value_or_from_self("state")

    class Meta:
        ordering = ("id",)
        indexes = [models.Index(fields=["-updated_on"])]

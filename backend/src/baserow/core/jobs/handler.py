import logging
from typing import Optional, Type, List

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.core.cache import cache
from django.db.models import QuerySet

from baserow.core.utils import Progress

from .types import AnyJob
from .registries import job_type_registry
from .exceptions import (
    JobDoesNotExist,
    MaxJobCountExceeded,
)
from .models import Job
from .tasks import run_async_job

from .cache import job_progress_key

logger = logging.getLogger(__name__)


class JobHandler:
    def run(self, job: AnyJob):
        def progress_updated(percentage, state):
            """
            Every time the progress of the job changes, this callback function is
            called. If the percentage or the state has changed, the job will be updated.
            """

            nonlocal job

            if job.progress_percentage != percentage:
                job.progress_percentage = percentage
                changed = True

            if state is not None and job.state != state:
                job.state = state
                changed = True

            if changed:
                # The progress must also be stored in the Redis cache. Because we're
                # currently in a transaction, other database connections don't know
                # about the progress and this way, we can still communicate it to
                # the user.
                cache.set(
                    job_progress_key(job.id),
                    {
                        "progress_percentage": job.progress_percentage,
                        "state": job.state,
                    },
                    timeout=None,
                )
                job.save()

        progress = Progress(100)
        progress.register_updated_event(progress_updated)

        job_type = job_type_registry.get_by_model(job.specific_class)

        return job_type.run(job.specific, progress)

    @staticmethod
    def get_job(
        user: AbstractUser,
        job_id: int,
        job_model: Optional[Type[AnyJob]] = None,
        base_queryset: Optional[QuerySet] = None,
    ) -> Job:
        """
        Returns the job corresponding to the given id.

        :param job_id: The job id we want to fetch.
        :param job_model: An optional Job model.
        :base_queryset: An optional base queryset to use instead of the default one.
        :return: the job.
        """

        if not job_model:
            job_model = Job

        if base_queryset is None:
            base_queryset = job_model.objects

        try:
            return base_queryset.select_related("user").get(id=job_id, user_id=user.id)
        except Job.DoesNotExist:
            raise JobDoesNotExist(f"The job with id {job_id} does not exist.")

    def get_jobs_for_user(self, user: AbstractUser) -> List[Job]:
        """
        Returns all jobs belonging to the specified user.

        :param user: The user we want the jobs for
        :return: A list of jobs
        """

        return Job.objects.filter(user=user).select_related("content_type")

    def create_and_start_job(
        self, user: AbstractUser, job_type_name: str, **kwargs
    ) -> Job:
        """
        Creates a new job and schedule the asynchronous task.

        :param user: The user whom launch the task.
        :param job_type_name: The job type we want to launch.
        :return: The newly created job.
        """

        job_type = job_type_registry.get(job_type_name)
        model_class = job_type.model_class

        # Check how many job of same type are running simultaneously. If count > max
        # we don't want to create a new one.
        running_jobs = model_class.objects.filter(user_id=user.id).is_running()
        if len(running_jobs) >= job_type.max_count:
            raise MaxJobCountExceeded(
                f"You can only launch {job_type.max_count} {job_type_name} job(s) at "
                "the same time."
            )

        job_values = job_type.prepare_values(kwargs, user)
        job = model_class.objects.create(user=user, **job_values)
        job_type.after_job_creation(job, kwargs)

        transaction.on_commit(lambda: run_async_job.delay(job.id))
        return job

    def clean_up_jobs(self):
        """
        Execute the cleanup method of all job types.
        """

        for job_type in job_type_registry.get_all():
            job_type.clean_up_jobs()

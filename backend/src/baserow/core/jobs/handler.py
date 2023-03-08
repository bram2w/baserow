from typing import List, Optional, Type

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from baserow.core.utils import Progress

from .cache import job_progress_key
from .constants import JOB_FAILED, JOB_PENDING
from .exceptions import JobDoesNotExist, MaxJobCountExceeded
from .models import Job
from .registries import job_type_registry
from .tasks import run_async_job
from .types import AnyJob


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

        job_type = job_type_registry.get_by_model(job)

        return job_type.run(job, progress)

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

    def get_jobs_for_user(
        self,
        user: AbstractUser,
        filter_states: Optional[List[str]],
        filter_ids: Optional[List[int]],
    ) -> QuerySet:
        """
        Returns all jobs belonging to the specified user.

        :param user: The user we want the jobs for.
        :param filter_states: A list of states that the jobs should have, or not
            have if prefixed with a !.
        :param filter_ids: A list of specific job ids to return.
        :return: A QuerySet with the filtered jobs for the user.
        """

        def get_job_states_filter(states):
            states_q = Q()
            for state in states:
                if state.startswith("!"):
                    states_q &= ~Q(state=state[1:])
                else:
                    states_q |= Q(state=state)
            return states_q

        queryset = Job.objects.filter(user=user).order_by("-updated_on")

        if filter_states:
            queryset = queryset.filter(get_job_states_filter(filter_states))

        if filter_ids:
            queryset = queryset.filter(id__in=filter_ids)

        return queryset.select_related("content_type")

    def get_pending_or_running_jobs(
        self,
        job_type_name: str,
    ) -> QuerySet:
        """
        Returns a queryset of pending or running jobs of a provided job type
        that can be further filtered.

        :param job_type_name: The job type for which we want the queryset.
        :return: Queryset of all pending or running jobs of the job type.
        """

        job_type = job_type_registry.get(job_type_name)
        model_class = job_type.model_class
        return model_class.objects.filter().is_pending_or_running()

    def create_and_start_job(
        self, user: AbstractUser, job_type_name: str, sync=False, **kwargs
    ) -> Job:
        """
        Creates a new job and schedule the asynchronous task.

        :param user: The user whom launch the task.
        :param job_type_name: The job type we want to launch.
        :param sync: True if you want to execute the job immediately.

        :return: The newly created job.
        """

        job_type = job_type_registry.get(job_type_name)
        model_class = job_type.model_class

        # Check how many job of same type are running simultaneously. If count > max
        # we don't want to create a new one.
        running_jobs = model_class.objects.filter(
            user_id=user.id
        ).is_pending_or_running()
        if len(running_jobs) >= job_type.max_count:
            raise MaxJobCountExceeded(
                f"You can only launch {job_type.max_count} {job_type_name} job(s) at "
                "the same time."
            )

        job_values = job_type.prepare_values(kwargs, user)
        job = model_class.objects.create(user=user, **job_values)
        job_type.after_job_creation(job, kwargs)

        if sync:
            run_async_job(job.id)
            job.refresh_from_db()
        else:

            # This wrapper ensure the job doesn't stay in pending state if something
            # goes wrong during the delay call. This is related to the redis connection
            # failure that triggers a sys.exit(1) to be called in gunicorn.
            def call_async_job_safe():
                try:
                    run_async_job.delay(job.id)
                except BaseException as e:
                    job.refresh_from_db()
                    if job.state == JOB_PENDING:
                        job.state = JOB_FAILED
                        job.error = str(e)
                        job.human_readable_error = (
                            f"Something went wrong during the job({job.id}) execution."
                        )
                        job.save()
                    raise

            transaction.on_commit(call_async_job_safe)

        return job

    def clean_up_jobs(self):
        """
        Terminate running jobs after the soft limit and delete expired jobs.
        """

        # Delete old job
        limit_date = timezone.now() - timezone.timedelta(
            minutes=(settings.BASEROW_JOB_EXPIRATION_TIME_LIMIT)
        )
        for job_to_delete in Job.objects.filter(
            created_on__lte=limit_date
        ).is_finished():
            job_type = job_type_registry.get_by_model(job_to_delete.specific)
            job_type.before_delete(job_to_delete.specific)
            job_to_delete.delete()

        # Expire non expired jobs
        limit_date = timezone.now() - timezone.timedelta(
            seconds=(settings.BASEROW_JOB_SOFT_TIME_LIMIT + 1)
        )

        (
            Job.objects.filter(created_on__lte=limit_date)
            .is_pending_or_running()
            .update(
                state=JOB_FAILED,
                human_readable_error=(
                    "Something went wrong during the file_import job execution."
                ),
                error="Unknown error",
                updated_on=timezone.now(),
            )
        )

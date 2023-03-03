from datetime import timedelta

from django.conf import settings

from baserow.config.celery import app
from baserow.core.jobs.registries import job_type_registry


@app.task(
    bind=True,
    queue="export",
    soft_time_limit=settings.BASEROW_JOB_SOFT_TIME_LIMIT,
)
def run_async_job(self, job_id: int):
    """Run the job task asynchronously"""

    from django.core.cache import cache

    from celery.exceptions import SoftTimeLimitExceeded

    from baserow.core.jobs.constants import JOB_FAILED, JOB_FINISHED, JOB_STARTED
    from baserow.core.jobs.handler import JobHandler
    from baserow.core.jobs.models import Job

    from .cache import job_progress_key

    job = Job.objects.get(id=job_id).specific
    job_type = job_type_registry.get_by_model(job)
    job.state = JOB_STARTED
    job.save(update_fields=("state",))

    try:
        with job_type.transaction_atomic_context(job):
            JobHandler().run(job)

        job.state = JOB_FINISHED
        # Don't override the other properties that have been set during the
        # progress update.
        job.save(update_fields=("state",))
    except BaseException as e:  # We also want to catch SystemExit exception here.
        error = f"Something went wrong during the {job_type.type} job execution."

        exception_mapping = {
            SoftTimeLimitExceeded: f"The {job_type.type} job took too long and was "
            "timed out."
        }
        exception_mapping.update(job_type.job_exceptions_map)

        for exception, error_message in exception_mapping.items():
            if isinstance(e, exception):
                error = error_message.format(e=e)
                break

        job.state = JOB_FAILED
        job.error = str(e)
        job.human_readable_error = error

        # Don't override the other properties that have been set during the
        # progress update.
        job.save(
            update_fields=(
                "state",
                "error",
                "human_readable_error",
            )
        )

        # Allow a job_type to modify job after an error
        job_type.on_error(job.specific, e)

        raise
    finally:
        # Delete the import job cached entry because the transaction has been committed
        # and the Job entry now contains the latest data.
        cache.delete(job_progress_key(job.id))


# noinspection PyUnusedLocal
@app.task(
    bind=True,
)
def clean_up_jobs(self):
    """
    Execute job cleanup for each job types if they need to cleanup something like files
    or old jobs.
    """

    from baserow.core.jobs.handler import JobHandler

    JobHandler().clean_up_jobs()


# noinspection PyUnusedLocal
@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        timedelta(minutes=settings.BASEROW_JOB_CLEANUP_INTERVAL_MINUTES),
        clean_up_jobs.s(),
    )

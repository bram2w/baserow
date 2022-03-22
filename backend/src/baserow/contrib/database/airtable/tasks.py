import logging

from django.conf import settings

from baserow.config.celery import app


logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    queue="export",
    soft_time_limit=settings.BASEROW_AIRTABLE_IMPORT_SOFT_TIME_LIMIT,
)
def run_import_from_airtable(self, job_id: int):
    """
    Starts the Airtable import job. This task must run after the job has been created.

    :param job_id: The id related to the job that must be started.
    """

    from celery.exceptions import SoftTimeLimitExceeded
    from pytz import timezone as pytz_timezone
    from requests.exceptions import RequestException

    from django.db import transaction
    from django.core.cache import cache

    from baserow.core.signals import application_created
    from baserow.core.utils import Progress
    from baserow.contrib.database.airtable.models import AirtableImportJob
    from baserow.contrib.database.airtable.handler import AirtableHandler
    from baserow.contrib.database.airtable.exceptions import (
        AirtableShareIsNotABase,
        AirtableBaseNotPublic,
    )
    from baserow.contrib.database.airtable.constants import (
        AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED,
        AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED,
    )

    from .cache import airtable_import_job_progress_key

    job = AirtableImportJob.objects.select_related("group").get(id=job_id)

    def progress_updated(percentage, state):
        """
        Every time the progress of the import changes, this callback function is
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
            # currently in a transaction, other database connections don't know about
            # the progress and this way, we can still communite it to the user.
            cache.set(
                airtable_import_job_progress_key(job.id),
                {"progress_percentage": job.progress_percentage, "state": job.state},
                timeout=None,
            )
            job.save()

    progress = Progress(100)
    progress.register_updated_event(progress_updated)

    kwargs = {}

    if job.timezone is not None:
        kwargs["timezone"] = pytz_timezone(job.timezone)

    try:
        with transaction.atomic():
            databases, id_mapping = AirtableHandler.import_from_airtable_to_group(
                job.group,
                job.airtable_share_id,
                progress_builder=progress.create_child_builder(
                    represents_progress=progress.total
                ),
                **kwargs
            )

            # The web-frontend needs to know about the newly created database, so we
            # call the application_created signal.
            for database in databases:
                application_created.send(self, application=database, user=None)

        job.state = AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED
        job.database = databases[0]
        # Don't override the other properties that have been set during the
        # progress update.
        job.save(update_fields=("state", "database"))
    except Exception as e:
        exception_mapping = {
            SoftTimeLimitExceeded: "The import job took too long and was timed out.",
            RequestException: "The Airtable server could not be reached.",
            AirtableBaseNotPublic: "The Airtable base is not publicly shared.",
            AirtableShareIsNotABase: "The shared link is not a base. It's probably a "
            "view and the Airtable import tool only supports shared bases.",
        }
        error = "Something went wrong while importing the Airtable base."

        for exception, error_message in exception_mapping.items():
            if isinstance(e, exception):
                error = error_message
                break

        job.state = AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED
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

        raise e
    finally:
        # Delete the import job cached entry because the transaction has been committed
        # and the AirtableImportJob entry now contains the latest data.
        cache.delete(airtable_import_job_progress_key(job.id))

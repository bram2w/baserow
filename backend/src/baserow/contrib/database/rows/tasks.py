from datetime import datetime, time, timedelta, timezone

from django.conf import settings

from baserow.config.celery import app


@app.task(bind=True, queue="export")
def clean_up_row_history_entries(self):
    """
    Execute job cleanup for row history entries.
    """

    from .history import RowHistoryHandler

    older_than_days = timedelta(days=settings.BASEROW_ROW_HISTORY_RETENTION_DAYS)

    cutoff_datetime = datetime.combine(
        datetime.now(tz=timezone.utc) - older_than_days, time.min
    )
    RowHistoryHandler.delete_entries_older_than(cutoff_datetime)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    every = timedelta(minutes=settings.BASEROW_ROW_HISTORY_CLEANUP_INTERVAL_MINUTES)

    sender.add_periodic_task(every, clean_up_row_history_entries.s())

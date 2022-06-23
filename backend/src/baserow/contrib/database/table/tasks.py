from django.conf import settings

from baserow.config.celery import app


@app.task(queue="export")
def run_row_count_job():
    """
    Runs the row count job to keep track of how many rows
    are being used by each table.
    """

    from baserow.contrib.database.table.handler import TableHandler

    TableHandler.count_rows()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    if settings.BASEROW_COUNT_ROWS_ENABLED:
        sender.add_periodic_task(
            settings.ROW_COUNT_INTERVAL,
            run_row_count_job.s(),
        )

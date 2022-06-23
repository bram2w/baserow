from django.conf import settings

from baserow.config.celery import app


@app.task(queue=settings.BASEROW_GROUP_STORAGE_USAGE_QUEUE)
def run_calculate_storage():
    """
    Runs the calculate storage job to keep track
    of how many mb of memory has been used
    via files by a group
    """

    from baserow.core.usage.handler import UsageHandler

    UsageHandler.calculate_storage_usage()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    if settings.BASEROW_GROUP_STORAGE_USAGE_ENABLED:
        sender.add_periodic_task(
            settings.USAGE_CALCULATION_INTERVAL,
            run_calculate_storage.s(),
        )

from datetime import timedelta

from django.conf import settings

from baserow.config.celery import app


# noinspection PyUnusedLocal
@app.task(
    bind=True,
)
def mark_old_trash_for_permanent_deletion(self):
    from baserow.core.trash.handler import TrashHandler

    TrashHandler.mark_old_trash_for_permanent_deletion()


# noinspection PyUnusedLocal
@app.task(
    bind=True,
)
def permanently_delete_marked_trash(self):
    from baserow.core.trash.handler import TrashHandler

    TrashHandler.permanently_delete_marked_trash()


# noinspection PyUnusedLocal
@app.on_after_finalize.connect
def setup_period_trash_tasks(sender, **kwargs):
    sender.add_periodic_task(
        timedelta(minutes=settings.OLD_TRASH_CLEANUP_CHECK_INTERVAL_MINUTES),
        mark_old_trash_for_permanent_deletion.s(),
    )
    sender.add_periodic_task(
        timedelta(minutes=settings.OLD_TRASH_CLEANUP_CHECK_INTERVAL_MINUTES),
        permanently_delete_marked_trash.s(),
    )

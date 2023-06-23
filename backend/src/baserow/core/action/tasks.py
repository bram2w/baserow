from datetime import timedelta

from django.conf import settings

from baserow.config.celery import app

# noinspection PyUnusedLocal
from baserow.core.action.handler import ActionHandler


@app.task(bind=True, queue="export")
def cleanup_old_actions(self):
    ActionHandler.clean_up_old_undoable_actions()


# noinspection PyUnusedLocal
@app.on_after_finalize.connect
def setup_periodic_action_tasks(sender, **kwargs):
    sender.add_periodic_task(
        timedelta(minutes=settings.OLD_ACTION_CLEANUP_INTERVAL_MINUTES),
        cleanup_old_actions.s(),
    )

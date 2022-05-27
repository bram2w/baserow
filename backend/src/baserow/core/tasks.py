from django.conf import settings

from baserow.config.celery import app
from .action.tasks import setup_periodic_action_tasks, cleanup_old_actions
from .trash.tasks import (
    permanently_delete_marked_trash,
    mark_old_trash_for_permanent_deletion,
    setup_period_trash_tasks,
)


@app.task(
    bind=True,
    queue="export",
    time_limit=settings.BASEROW_SYNC_TEMPLATES_TIME_LIMIT,
)
def sync_templates_task(self):
    from baserow.core.handler import CoreHandler

    CoreHandler().sync_templates()


__all__ = [
    "permanently_delete_marked_trash",
    "mark_old_trash_for_permanent_deletion",
    "setup_period_trash_tasks",
    "cleanup_old_actions",
    "setup_periodic_action_tasks",
    "sync_templates_task",
]

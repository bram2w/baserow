from datetime import timedelta

from django.conf import settings

from celery_singleton import Singleton

from baserow.config.celery import app
from baserow.core.user_templates.handler import UserTemplateHandler

DELETE_ORPHANED_USER_TEMPLATE_WORKSPACES_TIME_LIMIT = (
    60 * settings.BASEROW_JOB_CLEANUP_INTERVAL_MINUTES
)


@app.task(
    base=Singleton,
    raise_on_duplicate=False,
    bind=True,
    queue="export",
    soft_time_limit=DELETE_ORPHANED_USER_TEMPLATE_WORKSPACES_TIME_LIMIT,
    time_limit=DELETE_ORPHANED_USER_TEMPLATE_WORKSPACES_TIME_LIMIT,
    lock_expiry=DELETE_ORPHANED_USER_TEMPLATE_WORKSPACES_TIME_LIMIT,
)
def delete_orphaned_user_template_workspaces(self):
    """
    Deletes the workspaces and archives left behind by create user template jobs
    that didn't create their template.
    """

    UserTemplateHandler().delete_content_of_unfinished_jobs()


# noinspection PyUnusedLocal
@app.on_after_finalize.connect
def setup_periodic_user_template_tasks(sender, **kwargs):
    sender.add_periodic_task(
        timedelta(minutes=settings.BASEROW_JOB_CLEANUP_INTERVAL_MINUTES),
        delete_orphaned_user_template_workspaces.s(),
    )

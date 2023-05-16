import traceback

from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from celery_singleton import DuplicateTaskError, Singleton
from loguru import logger

from baserow.config.celery import app
from baserow.contrib.database.views.handler import ViewHandler, ViewIndexingHandler
from baserow.contrib.database.views.models import View

AUTO_INDEX_CACHE_KEY = "auto_index_view_cache_key"


def get_auto_index_cache_key(view_id):
    return f"{AUTO_INDEX_CACHE_KEY}:{view_id}"


@app.task(
    base=Singleton,
    queue="export",
    lock_expiry=settings.AUTO_INDEX_LOCK_EXPIRY,
    raise_on_duplicate=True,
)
@transaction.atomic()
def update_view_index(view_id: int):
    """
    Create/update the index for the provided view if needed.

    :param view_id: The id of the view for which the index should be updated.
    """

    try:
        view = ViewHandler().get_view(
            view_id, base_queryset=View.objects.prefetch_related("viewsort_set")
        )
        ViewIndexingHandler.update_index(view)
    finally:
        # check for any pending view index updates and schedule them out of this
        # singleton task to avoid concurrency issues
        _check_for_pending_view_index_updates.delay(view_id)


@app.task(queue="export")
def _check_for_pending_view_index_updates(view_id):
    """
    Checks if there are any pending view index updates and schedules them.
    """

    if cache.delete(get_auto_index_cache_key(view_id)):
        _schedule_view_index_update(view_id)


def _schedule_view_index_update(view_id: int):
    """
    Schedules a view index update for the provided view id. If the view index
    update is already scheduled then just add the view_id in the cache so that
    `update_view_index` will re-schedule itself at the end.

    :param view_id: The id of the view for which the index should be updated.
    """

    try:
        update_view_index.delay(view_id)
    except DuplicateTaskError:
        # Add the view_id in the cache so that `update_view_index` will
        # re-schedule itself at the end of the currently running task.
        cache.set(
            get_auto_index_cache_key(view_id),
            True,
            timeout=settings.AUTO_INDEX_LOCK_EXPIRY * 2,
        )
    except Exception as exc:  # nosec
        logger.error("Failed to schedule index update because of {e}", e=str(exc))
        traceback.print_exc()


def schedule_view_index_update(view_id: int):
    """
    Schedules a view index update for the provided view id. If the view index
    update is already scheduled then just add the view_id in the cache so that
    `update_view_index` will re-schedule itself at the end.

    :param view_id: The id of the view for which the index should be updated.
    """

    if not settings.AUTO_INDEX_VIEW_ENABLED:
        return

    transaction.on_commit(lambda: _schedule_view_index_update(view_id))

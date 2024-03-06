import traceback

from django.conf import settings
from django.db import transaction

from celery_singleton import DuplicateTaskError
from loguru import logger

__all__ = ["enqueue_task_on_commit_swallowing_any_exceptions"]


def enqueue_task_on_commit_swallowing_any_exceptions(on_commit_callable):
    """
    Given a Celery task, this function can be passed to a
    `transaction.on_commit` call. In the event that the task's
    `delay` call fails, it will ensure that we try and catch
    the exception, log what happened, and not fail hard.
    """

    def _inner():
        exc = None
        try:
            on_commit_callable()
        except DuplicateTaskError as e:
            exc = e
            # If the task implements `Singleton` and we've
            # detected that it's a duplicate, log it and continue.
            logger.debug(f"Duplicate task detected: {e.task_id}")
        except Exception as e:
            exc = e
            logger.error(f"Encountered an error enqueuing task: {str(e)}")
        finally:
            if exc:
                if settings.TESTS:
                    # If we're running tests, raise the exception so
                    # that we can assert its existence properly.
                    raise exc
                traceback.print_exc()

    in_transaction = not transaction.get_autocommit()
    if not in_transaction and settings.TESTS:
        logger.warning(
            "Skipping enqueuing end of transaction job in this test as you "
            "are not running inside of a transaction. If you want this job to run"
            "as part of your test make sure to wrap the part of the test you want it"
            "to run at the end of in a transaction.atomic block."
        )
    else:
        transaction.on_commit(_inner)

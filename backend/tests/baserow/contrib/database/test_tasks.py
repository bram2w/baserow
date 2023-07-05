from unittest.mock import Mock, patch

from django.db import transaction

import pytest
from redis.exceptions import RedisError

from baserow.contrib.database.tasks import (
    enqueue_task_on_commit_swallowing_any_exceptions,
)


@pytest.mark.django_db
@patch("django.db.transaction.on_commit")
def test_enqueue_task_with_exception_handling_logs_on_delay_exception(mock_commit):
    task = Mock()
    task.delay.side_effect = RedisError("connection error")
    on_commit_callable = Mock(return_value=task)

    try:
        with transaction.atomic():
            enqueue_task_on_commit_swallowing_any_exceptions(on_commit_callable)
    except Exception:
        pytest.fail("enqueue_task_with_exception_handling raised an exception.")

    assert mock_commit.called

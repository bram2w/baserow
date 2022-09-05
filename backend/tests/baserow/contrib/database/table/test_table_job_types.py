from django.db import transaction

import pytest

from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.job_types import DuplicateTableJobType
from baserow.contrib.database.table.models import Table
from baserow.core.action.handler import ActionHandler
from baserow.core.action.scopes import ApplicationActionScopeType
from baserow.core.jobs.constants import JOB_FINISHED
from baserow.core.jobs.handler import JobHandler
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid


@pytest.mark.django_db(transaction=True)
def test_can_submit_duplicate_table_job(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database, user=user)

    assert Table.objects.count() == 1

    duplicate_table_job = JobHandler().create_and_start_job(
        user,
        DuplicateTableJobType.type,
        table_id=table.id,
    )

    assert Table.objects.count() == 2

    duplicate_table_job.refresh_from_db()
    assert duplicate_table_job.state == JOB_FINISHED
    assert duplicate_table_job.original_table_id == table.id
    assert duplicate_table_job.duplicated_table_id is not None

    duplicated_table = TableHandler().get_table(duplicate_table_job.duplicated_table_id)
    assert duplicated_table.name == f"{table.name} 2"

    # assert table_id is mandatory
    with pytest.raises(KeyError):
        JobHandler().create_and_start_job(user, DuplicateTableJobType.type)

    assert Table.objects.count() == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.undo_redo
def test_can_undo_duplicate_table_job(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database, user=user)

    JobHandler().create_and_start_job(
        user,
        DuplicateTableJobType.type,
        table_id=table.id,
        user_session_id=session_id,
    )

    assert Table.objects.count() == 2

    with transaction.atomic():
        actions_undone = ActionHandler.undo(
            user,
            [ApplicationActionScopeType.value(application_id=database.id)],
            session_id,
        )
        assert_undo_redo_actions_are_valid(actions_undone, [DuplicateTableJobType])

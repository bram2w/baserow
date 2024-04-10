from django.db import transaction

import pytest

from baserow.core.action.handler import ActionHandler
from baserow.core.action.scopes import WorkspaceActionScopeType
from baserow.core.exceptions import ApplicationDoesNotExist, UserNotInWorkspace
from baserow.core.handler import CoreHandler
from baserow.core.job_types import DuplicateApplicationJobType
from baserow.core.jobs.constants import JOB_FINISHED
from baserow.core.jobs.handler import JobHandler
from baserow.core.jobs.tasks import run_async_job
from baserow.core.models import Application
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid


@pytest.mark.django_db
def test_value_preparation_for_duplicate_application_job(data_fixture):
    user = data_fixture.create_user()
    ext_database = data_fixture.create_database_application()

    with pytest.raises(UserNotInWorkspace):
        job = JobHandler().create_and_start_job(
            user,
            DuplicateApplicationJobType.type,
            application_id=ext_database.id,
        )
        run_async_job(job.id)

    with pytest.raises(ApplicationDoesNotExist):
        job = JobHandler().create_and_start_job(
            user,
            DuplicateApplicationJobType.type,
            application_id=9999,
        )
        run_async_job(job.id)

    with pytest.raises(KeyError):
        job = JobHandler().create_and_start_job(
            user,
            DuplicateApplicationJobType.type,
        )
        run_async_job(job.id)


@pytest.mark.django_db(transaction=True)
def test_can_submit_duplicate_application_job(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    application_type = "database"
    application_name = "My Application"

    application = CoreHandler().create_application(
        user, workspace, application_type, name=application_name
    )

    assert Application.objects.count() == 1

    duplicate_application_job = JobHandler().create_and_start_job(
        user,
        DuplicateApplicationJobType.type,
        application_id=application.id,
    )

    assert Application.objects.count() == 2

    duplicate_application_job.refresh_from_db()

    assert duplicate_application_job.state == JOB_FINISHED
    assert duplicate_application_job.original_application_id == application.id
    assert duplicate_application_job.duplicated_application_id is not None

    duplicated_application = CoreHandler().get_application(
        duplicate_application_job.duplicated_application_id
    )
    assert duplicated_application.name == f"{application_name} 2"

    # assert that user_session_id and user_websocket_id are not mandatory
    # and the job can be called synchronously
    duplicate_application_job_2 = JobHandler().create_and_start_job(
        user, DuplicateApplicationJobType.type, application_id=application.id, sync=True
    )

    assert Application.objects.count() == 3

    assert duplicate_application_job_2.state == JOB_FINISHED
    assert duplicate_application_job_2.original_application_id == application.id
    assert duplicate_application_job_2.duplicated_application_id is not None
    duplicated_application_2 = CoreHandler().get_application(
        duplicate_application_job_2.duplicated_application_id
    )
    assert duplicated_application_2.name == f"{application_name} 3"

    # assert application_id is mandatory
    with pytest.raises(KeyError):
        duplicate_application_job_2 = JobHandler().create_and_start_job(
            user, DuplicateApplicationJobType.type, sync=True
        )

    assert Application.objects.count() == 3


@pytest.mark.django_db(transaction=True)
def test_can_undo_duplicate_application_job(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    application_type = "database"
    application_name = "My Application"

    application = CoreHandler().create_application(
        user, workspace, application_type, name=application_name
    )

    JobHandler().create_and_start_job(
        user,
        DuplicateApplicationJobType.type,
        application_id=application.id,
        sync=True,
    )

    assert Application.objects.count() == 2

    with transaction.atomic():
        actions_undone = ActionHandler.undo(
            user,
            [WorkspaceActionScopeType.value(workspace_id=workspace.id)],
            session_id,
        )

        assert_undo_redo_actions_are_valid(
            actions_undone, [DuplicateApplicationJobType]
        )

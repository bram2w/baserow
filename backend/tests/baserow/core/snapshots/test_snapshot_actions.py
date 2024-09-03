import contextlib
from unittest.mock import patch

from django.db import transaction

import pytest

from baserow.core.action.registries import action_type_registry
from baserow.core.jobs.constants import JOB_FINISHED
from baserow.core.snapshots.actions import (
    CreateSnapshotActionType,
    DeleteSnapshotActionType,
    RestoreSnapshotActionType,
)
from baserow.core.snapshots.handler import SnapshotHandler


@pytest.mark.django_db
@patch(
    "baserow.core.snapshots.job_types.CreateSnapshotJobType.transaction_atomic_context",
    new=contextlib.nullcontext,
)
@patch("baserow.core.action.signals.action_done.send")
def test_create_snapshot_action_type(
    send_mock, data_fixture, django_capture_on_commit_callbacks
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_database_application(workspace=workspace)

    with django_capture_on_commit_callbacks(execute=True):
        result = SnapshotHandler().start_create_job(
            application.id, user, "test snapshot"
        )

    snapshot = result["snapshot"]
    job = result["job"]

    job.refresh_from_db()
    assert job.state == JOB_FINISHED

    assert send_mock.call_count == 1
    assert send_mock.call_args[1]["action_type"].type == CreateSnapshotActionType.type

    assert snapshot.name == "test snapshot"
    assert snapshot.snapshot_from_application_id == application.id
    assert snapshot.snapshot_to_application_id is None


@pytest.mark.django_db
@patch(
    "baserow.core.snapshots.job_types.RestoreSnapshotJobType.transaction_atomic_context",
    new=contextlib.nullcontext,
)
@patch("baserow.core.action.signals.action_done.send")
def test_restore_snapshot_action_type(
    send_mock, data_fixture, django_capture_on_commit_callbacks
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    from_application = data_fixture.create_database_application(workspace=workspace)
    to_application = data_fixture.create_database_application(
        workspace=workspace, name="test"
    )
    snapshot = data_fixture.create_snapshot(
        snapshot_from_application=from_application,
        snapshot_to_application=to_application,
        name="snapshot",
        created_by=user,
    )

    with django_capture_on_commit_callbacks(execute=True):
        job = SnapshotHandler().start_restore_job(snapshot.id, user)

    job.refresh_from_db()
    assert job.state == JOB_FINISHED

    assert send_mock.call_count == 1
    assert send_mock.call_args[1]["action_type"].type == RestoreSnapshotActionType.type

    assert snapshot.snapshot_to_application.name == "test"


@pytest.mark.django_db(transaction=True)
def test_delete_snapshot_action_type(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    from_application = data_fixture.create_database_application(workspace=workspace)
    to_application = data_fixture.create_database_application(
        workspace=workspace, name="test"
    )
    snapshot = data_fixture.create_snapshot(
        snapshot_from_application=from_application,
        snapshot_to_application=to_application,
        name="snapshot",
        created_by=user,
    )

    assert SnapshotHandler().list(from_application.id, user).count() == 1

    with transaction.atomic():
        action_type_registry.get(DeleteSnapshotActionType.type).do(user, snapshot.id)

    assert SnapshotHandler().list(from_application.id, user).count() == 0

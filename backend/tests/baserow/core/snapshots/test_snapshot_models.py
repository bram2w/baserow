from django.apps import apps

import pytest

from baserow.core.jobs.constants import JOB_FAILED, JOB_FINISHED, JOB_PENDING
from baserow.core.models import Snapshot
from baserow.core.snapshots.models import CreateSnapshotJob


@pytest.mark.disabled_in_ci
def test_migration_remove_dangling_snapshots(
    data_fixture, migrator, teardown_table_metadata
):
    migrate_from = [
        ("core", "0078_usersource"),
    ]
    migrate_to = [("core", "0079_remove_dangling_snapshots")]

    migrator.migrate(migrate_from)

    user_model = apps.get_model("auth", "User")
    user = user_model()
    user.save()

    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    snapshotted_database = data_fixture.create_database_application(workspace=workspace)

    snapshot_finished = Snapshot.objects.create(
        snapshot_from_application=database,
        snapshot_to_application=None,
        created_by=user,
        name="snapshot finished",
    )
    CreateSnapshotJob.objects.create(
        user=user, state=JOB_FINISHED, snapshot=snapshot_finished
    )

    snapshot_pending = Snapshot.objects.create(
        snapshot_from_application=database,
        snapshot_to_application=None,
        created_by=user,
        name="snapshot pending",
    )
    CreateSnapshotJob.objects.create(
        user=user, state=JOB_PENDING, snapshot=snapshot_pending
    )

    snapshot_marked_for_deletion = Snapshot.objects.create(
        snapshot_from_application=database,
        snapshot_to_application=None,
        created_by=user,
        mark_for_deletion=True,
        name="marked for deletion",
    )
    CreateSnapshotJob.objects.create(
        user=user, state=JOB_FINISHED, snapshot=snapshot_marked_for_deletion
    )

    snapshot_failed_but_created = Snapshot.objects.create(
        snapshot_from_application=database,
        snapshot_to_application=snapshotted_database,
        created_by=user,
        mark_for_deletion=True,
        name="failed but exist",
    )
    CreateSnapshotJob.objects.create(
        user=user, state=JOB_FAILED, snapshot=snapshot_failed_but_created
    )

    dangling_snapshot = Snapshot.objects.create(
        snapshot_from_application=database,
        snapshot_to_application=None,
        created_by=user,
        name="marked for removal",
    )
    CreateSnapshotJob.objects.create(
        user=user, state=JOB_FAILED, snapshot=dangling_snapshot
    )

    assert Snapshot.objects.count() == 5

    migrator.migrate(migrate_to)

    assert Snapshot.objects.count() == 4
    snapshot_ids = set(Snapshot.objects.all().values_list("id", flat=True))
    assert snapshot_ids == {
        snapshot_finished.id,
        snapshot_pending.id,
        snapshot_marked_for_deletion.id,
        snapshot_failed_but_created.id,
    }

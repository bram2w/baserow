import pytest

from baserow.core.exceptions import UserNotInWorkspace
from baserow.core.jobs.constants import JOB_FAILED
from baserow.core.jobs.handler import JobHandler
from baserow.core.snapshots.job_types import CreateSnapshotJobType
from baserow.core.snapshots.models import Snapshot


@pytest.mark.django_db(transaction=True)
def test_no_dangling_snapshots_on_error(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace()
    database = data_fixture.create_database_application(workspace=workspace)

    snapshot = Snapshot.objects.create(
        snapshot_from_application=database,
        created_by=user,
        name="snapshot",
    )

    with pytest.raises(UserNotInWorkspace):
        job = JobHandler().create_and_start_job(
            user, CreateSnapshotJobType.type, sync=True, snapshot=snapshot
        )
        assert job.state == JOB_FAILED

    assert Snapshot.objects.count() == 0

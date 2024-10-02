from datetime import timedelta

from django.conf import settings
from django.utils import timezone

import pytest
from freezegun import freeze_time

from baserow.core.exceptions import UserNotInWorkspace
from baserow.core.jobs.constants import JOB_FAILED
from baserow.core.jobs.handler import JobHandler
from baserow.core.snapshots.job_types import CreateSnapshotJobType
from baserow.core.snapshots.models import Snapshot


@pytest.mark.django_db(transaction=True)
def test_dangling_snapshots_are_removed(data_fixture):
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

    # we still keep that snapshot
    assert Snapshot.objects.count() == 1

    assert Snapshot.objects.restorable().count() == 0
    assert Snapshot.objects.unusable().count() == 1

    # cleanup should remove stale snapshots along with a job
    with freeze_time(
        timezone.now()
        + timedelta(minutes=settings.BASEROW_JOB_EXPIRATION_TIME_LIMIT + 10)
    ):
        JobHandler().clean_up_jobs()
    assert Snapshot.objects.count() == 0

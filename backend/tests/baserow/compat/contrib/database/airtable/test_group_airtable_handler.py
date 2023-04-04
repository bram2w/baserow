from unittest.mock import patch

import pytest
import responses
from rest_framework.exceptions import ValidationError

from baserow.contrib.database.airtable.job_types import AirtableImportJobType
from baserow.core.exceptions import UserNotInWorkspace
from baserow.core.jobs.constants import JOB_PENDING
from baserow.core.jobs.exceptions import MaxJobCountExceeded
from baserow.core.jobs.handler import JobHandler


@pytest.mark.django_db(transaction=True)
@responses.activate
@pytest.mark.disabled_in_ci
@patch("baserow.core.jobs.handler.run_async_job")
def test_create_and_start_airtable_import_job_with_group(
    mock_run_async_job, data_fixture, group_compat_timebomb
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    workspace_2 = data_fixture.create_workspace()

    with pytest.raises(UserNotInWorkspace):
        JobHandler().create_and_start_job(
            user,
            AirtableImportJobType.type,
            group_id=workspace_2.id,
            airtable_share_url="https://airtable.com/shrXxmp0WmqsTkFWTz",
        )

    job = JobHandler().create_and_start_job(
        user,
        AirtableImportJobType.type,
        group_id=workspace.id,
        airtable_share_url="https://airtable.com/shrXxmp0WmqsTkFWTz",
    )
    assert job.user_id == user.id
    assert job.group_id == workspace.id
    assert job.airtable_share_id == "shrXxmp0WmqsTkFWTz"
    assert job.progress_percentage == 0
    assert job.state == "pending"
    assert job.error == ""

    mock_run_async_job.delay.assert_called_once()
    args = mock_run_async_job.delay.call_args
    assert args[0][0] == job.id


@pytest.mark.django_db
@responses.activate
@pytest.mark.disabled_in_ci
def test_create_and_start_airtable_import_job_while_other_job_is_running_with_group(
    data_fixture, group_compat_timebomb
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    data_fixture.create_airtable_import_job(user=user, state=JOB_PENDING)

    with pytest.raises(MaxJobCountExceeded):
        JobHandler().create_and_start_job(
            user,
            AirtableImportJobType.type,
            group_id=workspace.id,
            airtable_share_url="https://airtable.com/shrXxmp0WmqsTkFWTz",
        )


@pytest.mark.django_db
@responses.activate
@pytest.mark.disabled_in_ci
def test_create_and_start_airtable_import_job_without_group_or_workspace_id(
    data_fixture, group_compat_timebomb
):
    user = data_fixture.create_user()

    with pytest.raises(
        ValidationError,
        match="A `workspace_id` or `group_id` is "
        "required to execute an "
        "AirtableImportJob.",
    ):
        JobHandler().create_and_start_job(
            user,
            AirtableImportJobType.type,
            airtable_share_url="https://airtable.com/shrXxmp0WmqsTkFWTz",
        )

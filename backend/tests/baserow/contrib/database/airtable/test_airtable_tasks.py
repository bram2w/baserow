import pytest
import responses

from pytz import BaseTzInfo
from unittest.mock import patch
from celery.exceptions import SoftTimeLimitExceeded
from requests.exceptions import ConnectionError

from django.db import connections
from django.core.cache import cache

from baserow.core.utils import ChildProgressBuilder
from baserow.contrib.database.airtable.tasks import run_import_from_airtable
from baserow.contrib.database.airtable.models import AirtableImportJob
from baserow.contrib.database.airtable.constants import (
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_PENDING,
)
from baserow.contrib.database.airtable.cache import airtable_import_job_progress_key
from baserow.contrib.database.airtable.exceptions import AirtableShareIsNotABase


@pytest.mark.django_db(transaction=True, databases=["default", "default-copy"])
@responses.activate
@patch(
    "baserow.contrib.database.airtable.handler"
    ".AirtableHandler.import_from_airtable_to_group"
)
@patch("baserow.core.signals.application_created.send")
@pytest.mark.timeout(10)
def test_run_import_from_airtable(
    send_mock, mock_import_from_airtable_to_group, data_fixture
):
    # Somehow needed to activate the second connection.
    connections["default-copy"]

    created_database = data_fixture.create_database_application()

    def update_progress_slow(*args, **kwargs):
        nonlocal job
        nonlocal created_database

        progress_builder = kwargs["progress_builder"]
        progress = ChildProgressBuilder.build(progress_builder, 100)
        progress.increment(50, "test")

        # Check if the job has updated in the transaction
        job.refresh_from_db()
        assert job.progress_percentage == 50
        assert job.state == "test"

        # We're using the second connection to check if we can get the most recent
        # progress value while the transaction is still active.
        job_copy = AirtableImportJob.objects.using("default-copy").get(pk=job.id)
        # Normal progress is expected to be 0
        assert job_copy.progress_percentage == 0
        assert job_copy.state == AIRTABLE_EXPORT_JOB_DOWNLOADING_PENDING
        # Progress stored in Redis is expected to be accurate.
        assert job_copy.get_cached_progress_percentage() == 50
        assert job_copy.get_cached_state() == "test"

        progress.increment(50)

        return ([created_database], {})

    mock_import_from_airtable_to_group.side_effect = update_progress_slow

    job = data_fixture.create_airtable_import_job()

    with pytest.raises(AirtableImportJob.DoesNotExist):
        run_import_from_airtable(0)

    run_import_from_airtable(job.id)

    mock_import_from_airtable_to_group.assert_called_once()
    args = mock_import_from_airtable_to_group.call_args
    assert args[0][0].id == job.group.id
    assert args[0][1] == job.airtable_share_id
    assert isinstance(args[1]["progress_builder"], ChildProgressBuilder)
    assert args[1]["progress_builder"].represents_progress == 100
    assert "timezone" not in args[1]

    job = AirtableImportJob.objects.get(pk=job.id)
    assert job.progress_percentage == 100
    assert job.state == AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED
    assert job.database_id == created_database.id

    # The cache entry will be removed when when job completes.
    assert cache.get(airtable_import_job_progress_key(job.id)) is None

    job_copy = AirtableImportJob.objects.using("default-copy").get(pk=job.id)
    assert job_copy.progress_percentage == 100
    assert job_copy.state == AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED
    assert job_copy.get_cached_progress_percentage() == 100
    assert job_copy.get_cached_state() == AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED
    assert job_copy.database_id == created_database.id

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["application"].id == job.database_id
    assert send_mock.call_args[1]["user"] is None


@pytest.mark.django_db(transaction=True)
@responses.activate
@patch(
    "baserow.contrib.database.airtable.handler.AirtableHandler"
    ".import_from_airtable_to_group"
)
def test_run_import_from_airtable_failing_import(
    mock_import_from_airtable_to_group, data_fixture
):
    def update_progress_slow(*args, **kwargs):
        raise Exception("test-1")

    mock_import_from_airtable_to_group.side_effect = update_progress_slow

    job = data_fixture.create_airtable_import_job()

    with pytest.raises(Exception):
        run_import_from_airtable(job.id)

    job.refresh_from_db()
    assert job.state == AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED
    assert job.error == "test-1"
    assert (
        job.human_readable_error
        == "Something went wrong while importing the Airtable base."
    )


@pytest.mark.django_db(transaction=True)
@responses.activate
@patch(
    "baserow.contrib.database.airtable.handler.AirtableHandler"
    ".import_from_airtable_to_group"
)
def test_run_import_from_airtable_failing_time_limit(
    mock_import_from_airtable_to_group, data_fixture
):
    def update_progress_slow(*args, **kwargs):
        raise SoftTimeLimitExceeded("test")

    mock_import_from_airtable_to_group.side_effect = update_progress_slow

    job = data_fixture.create_airtable_import_job()

    with pytest.raises(SoftTimeLimitExceeded):
        run_import_from_airtable(job.id)

    job.refresh_from_db()
    assert job.state == AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED
    assert job.error == "SoftTimeLimitExceeded('test',)"
    assert job.human_readable_error == "The import job took too long and was timed out."


@pytest.mark.django_db(transaction=True)
@responses.activate
@patch(
    "baserow.contrib.database.airtable.handler.AirtableHandler"
    ".import_from_airtable_to_group"
)
def test_run_import_from_airtable_failing_connection_error(
    mock_import_from_airtable_to_group, data_fixture
):
    def update_progress_slow(*args, **kwargs):
        raise ConnectionError("connection error")

    mock_import_from_airtable_to_group.side_effect = update_progress_slow

    job = data_fixture.create_airtable_import_job()

    with pytest.raises(ConnectionError):
        run_import_from_airtable(job.id)

    job.refresh_from_db()
    assert job.state == AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED
    assert job.error == "connection error"
    assert job.human_readable_error == "The Airtable server could not be reached."


@pytest.mark.django_db(transaction=True)
@responses.activate
@patch(
    "baserow.contrib.database.airtable.handler.AirtableHandler"
    ".import_from_airtable_to_group"
)
def test_run_import_shared_view(mock_import_from_airtable_to_group, data_fixture):
    def update_progress_slow(*args, **kwargs):
        raise AirtableShareIsNotABase("The `shared_id` is not a base.")

    mock_import_from_airtable_to_group.side_effect = update_progress_slow

    job = data_fixture.create_airtable_import_job()

    with pytest.raises(AirtableShareIsNotABase):
        run_import_from_airtable(job.id)

    job.refresh_from_db()
    assert job.state == AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED
    assert job.error == "The `shared_id` is not a base."
    assert (
        job.human_readable_error
        == "The shared link is not a base. It's probably a view and the Airtable "
        "import tool only supports shared bases."
    )


@pytest.mark.django_db
@responses.activate
@patch(
    "baserow.contrib.database.airtable.handler"
    ".AirtableHandler.import_from_airtable_to_group"
)
def test_run_import_from_airtable_with_timezone(
    mock_import_from_airtable_to_group, data_fixture
):
    database = data_fixture.create_database_application()
    mock_import_from_airtable_to_group.return_value = [database], {}

    job = data_fixture.create_airtable_import_job(timezone="Europe/Amsterdam")

    with pytest.raises(AirtableImportJob.DoesNotExist):
        run_import_from_airtable(0)

    run_import_from_airtable(job.id)

    mock_import_from_airtable_to_group.assert_called_once()
    args = mock_import_from_airtable_to_group.call_args
    assert args[0][0].id == job.group.id
    assert args[0][1] == job.airtable_share_id
    assert isinstance(args[1]["progress_builder"], ChildProgressBuilder)
    assert args[1]["progress_builder"].represents_progress == 100
    assert isinstance(args[1]["timezone"], BaseTzInfo)
    assert str(args[1]["timezone"]) == "Europe/Amsterdam"

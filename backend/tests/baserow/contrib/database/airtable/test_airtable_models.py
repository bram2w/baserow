import pytest

from django.core.cache import cache

from baserow.contrib.database.airtable.models import AirtableImportJob
from baserow.contrib.database.airtable.constants import (
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_PENDING,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FILES,
    AIRTABLE_EXPORT_JOB_CONVERTING,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_BASE,
)
from baserow.contrib.database.airtable.cache import airtable_import_job_progress_key


@pytest.mark.django_db
def test_is_running_queryset(data_fixture):
    data_fixture.create_airtable_import_job(
        state=AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED
    )
    data_fixture.create_airtable_import_job(
        state=AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED
    )

    assert AirtableImportJob.objects.is_running().count() == 0

    data_fixture.create_airtable_import_job(
        state=AIRTABLE_EXPORT_JOB_DOWNLOADING_PENDING
    )
    data_fixture.create_airtable_import_job(state=AIRTABLE_EXPORT_JOB_DOWNLOADING_FILES)
    data_fixture.create_airtable_import_job(state=AIRTABLE_EXPORT_JOB_CONVERTING)
    data_fixture.create_airtable_import_job(state=AIRTABLE_EXPORT_JOB_DOWNLOADING_BASE)

    assert AirtableImportJob.objects.is_running().count() == 4


@pytest.mark.django_db
def test_cached_values(data_fixture):
    job = data_fixture.create_airtable_import_job(
        progress_percentage=10,
        state=AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED,
    )

    assert job.progress_percentage == 10
    assert job.state == AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED

    assert job.get_cached_progress_percentage() == 10
    assert job.get_cached_state() == AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED

    key = airtable_import_job_progress_key(0)
    cache.set(key, {"progress_percentage": 0, "state": "test"})

    assert job.get_cached_progress_percentage() == 10
    assert job.get_cached_state() == AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED

    key = airtable_import_job_progress_key(job.id)
    cache.set(key, {"progress_percentage": 20, "state": "something"})

    assert job.get_cached_progress_percentage() == 20
    assert job.get_cached_state() == "something"

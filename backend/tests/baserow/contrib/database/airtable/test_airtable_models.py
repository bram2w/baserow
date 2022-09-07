from django.core.cache import cache

import pytest

from baserow.contrib.database.airtable.constants import (
    AIRTABLE_EXPORT_JOB_CONVERTING,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_BASE,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FILES,
)
from baserow.contrib.database.airtable.models import AirtableImportJob
from baserow.core.jobs.cache import job_progress_key
from baserow.core.jobs.constants import (
    JOB_FAILED,
    JOB_FINISHED,
    JOB_PENDING,
    JOB_STARTED,
)


@pytest.mark.django_db
def test_is_running_queryset(data_fixture):
    data_fixture.create_airtable_import_job(state=JOB_FAILED)
    data_fixture.create_airtable_import_job(state=JOB_FINISHED)
    data_fixture.create_airtable_import_job(state=JOB_PENDING)

    assert AirtableImportJob.objects.is_running().count() == 0

    data_fixture.create_airtable_import_job(state=JOB_STARTED)
    data_fixture.create_airtable_import_job(state=AIRTABLE_EXPORT_JOB_DOWNLOADING_FILES)
    data_fixture.create_airtable_import_job(state=AIRTABLE_EXPORT_JOB_CONVERTING)
    data_fixture.create_airtable_import_job(state=AIRTABLE_EXPORT_JOB_DOWNLOADING_BASE)

    assert AirtableImportJob.objects.is_running().count() == 4


@pytest.mark.django_db
def test_cached_values(data_fixture):
    job = data_fixture.create_airtable_import_job(
        progress_percentage=10,
        state=JOB_FAILED,
    )

    assert job.progress_percentage == 10
    assert job.state == JOB_FAILED

    assert job.get_cached_progress_percentage() == 10
    assert job.get_cached_state() == JOB_FAILED

    key = job_progress_key(0)
    cache.set(key, {"progress_percentage": 0, "state": "test"})

    assert job.get_cached_progress_percentage() == 10
    assert job.get_cached_state() == JOB_FAILED

    key = job_progress_key(job.id)
    cache.set(key, {"progress_percentage": 20, "state": "something"})

    assert job.get_cached_progress_percentage() == 20
    assert job.get_cached_state() == "something"

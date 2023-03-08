from unittest.mock import patch

from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from baserow.contrib.database.airtable.models import AirtableImportJob


@pytest.mark.django_db(transaction=True)
@patch("baserow.core.jobs.handler.run_async_job")
def test_create_airtable_import_job(
    mock_run_import_from_airtable, data_fixture, api_client
):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    group_2 = data_fixture.create_group()

    response = api_client.post(
        reverse("api:jobs:list"),
        {
            "type": "airtable",
            "group_id": 0,
            "airtable_share_url": "https://airtable.com/shrxxxxxxxxxxxxxx",
        },
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"

    response = api_client.post(
        reverse("api:jobs:list"),
        {
            "type": "airtable",
            "group_id": group_2.id,
            "airtable_share_url": "https://airtable.com/shrxxxxxxxxxxxxxx",
        },
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.post(
        reverse("api:jobs:list"),
        {
            "type": "airtable",
        },
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json() == {
        "error": "ERROR_REQUEST_BODY_VALIDATION",
        "detail": {
            "group_id": [{"error": "This field is required.", "code": "required"}],
            "airtable_share_url": [
                {"error": "This field is required.", "code": "required"}
            ],
        },
    }

    response = api_client.post(
        reverse("api:jobs:list"),
        {
            "type": "airtable",
            "group_id": "not_int",
            "airtable_share_url": "https://airtable.com/test",
        },
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json() == {
        "error": "ERROR_REQUEST_BODY_VALIDATION",
        "detail": {
            "group_id": [{"error": "A valid integer is required.", "code": "invalid"}],
            "airtable_share_url": [
                {
                    "error": "The publicly shared Airtable URL is invalid.",
                    "code": "invalid",
                }
            ],
        },
    }

    response = api_client.post(
        reverse("api:jobs:list"),
        {
            "type": "airtable",
            "group_id": group.id,
            "airtable_share_url": "https://airtable.com/shrxxxxxxxxxxxxxx",
        },
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    airtable_import_job = AirtableImportJob.objects.all().first()
    assert airtable_import_job.group_id == group.id
    assert airtable_import_job.airtable_share_id == "shrxxxxxxxxxxxxxx"
    assert response.json() == {
        "id": airtable_import_job.id,
        "type": "airtable",
        "group_id": group.id,
        "airtable_share_id": "shrxxxxxxxxxxxxxx",
        "progress_percentage": 0,
        "state": "pending",
        "human_readable_error": "",
        "database": None,
    }
    mock_run_import_from_airtable.delay.assert_called()

    airtable_import_job.delete()
    response = api_client.post(
        reverse("api:jobs:list"),
        {
            "type": "airtable",
            "group_id": group.id,
            "airtable_share_url": "https://airtable.com/shrxxxxxxxxxxxxxx",
        },
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    airtable_import_job = AirtableImportJob.objects.all().first()
    assert airtable_import_job.group_id == group.id
    assert airtable_import_job.airtable_share_id == "shrxxxxxxxxxxxxxx"
    assert response.json() == {
        "id": airtable_import_job.id,
        "type": "airtable",
        "group_id": group.id,
        "airtable_share_id": "shrxxxxxxxxxxxxxx",
        "progress_percentage": 0,
        "state": "pending",
        "human_readable_error": "",
        "database": None,
    }

    response = api_client.post(
        reverse("api:jobs:list"),
        {
            "type": "airtable",
            "group_id": group.id,
            "airtable_share_url": "https://airtable.com/shrxxxxxxxxxxxxxx",
        },
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_MAX_JOB_COUNT_EXCEEDED"


@pytest.mark.django_db
def test_get_airtable_import_job(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    airtable_job_1 = data_fixture.create_airtable_import_job(user=user)
    airtable_job_2 = data_fixture.create_airtable_import_job()

    response = api_client.get(
        reverse(
            "api:jobs:item",
            kwargs={"job_id": airtable_job_2.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_JOB_DOES_NOT_EXIST"

    response = api_client.get(
        reverse(
            "api:jobs:item",
            kwargs={"job_id": airtable_job_1.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    json = response.json()
    assert json == {
        "id": airtable_job_1.id,
        "type": "airtable",
        "group_id": airtable_job_1.group_id,
        "airtable_share_id": "test",
        "progress_percentage": 0,
        "state": "pending",
        "human_readable_error": "",
        "database": None,
    }

    airtable_job_1.progress_percentage = 50
    airtable_job_1.state = "failed"
    airtable_job_1.human_readable_error = "Wrong"
    airtable_job_1.database = data_fixture.create_database_application()
    airtable_job_1.save()

    response = api_client.get(
        reverse(
            "api:jobs:item",
            kwargs={"job_id": airtable_job_1.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    json = response.json()
    assert json == {
        "id": airtable_job_1.id,
        "type": "airtable",
        "group_id": airtable_job_1.group_id,
        "airtable_share_id": "test",
        "progress_percentage": 50,
        "state": "failed",
        "human_readable_error": "Wrong",
        "database": {
            "id": airtable_job_1.database.id,
            "name": airtable_job_1.database.name,
            "order": 0,
            "type": "database",
            "group": {
                "id": airtable_job_1.database.group.id,
                "name": airtable_job_1.database.group.name,
            },
        },
    }

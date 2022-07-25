import pytest
import json
from unittest.mock import patch

from django.db import connection
from django.test.utils import override_settings
from django.shortcuts import reverse
from django.test.utils import CaptureQueriesContext

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from baserow.contrib.database.file_import.models import FileImportJob
from baserow.contrib.database.table.models import Table
from baserow.test_utils.helpers import independent_test_db_connection


@pytest.mark.django_db
def test_list_tables(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    database_2 = data_fixture.create_database_application()
    table_1 = data_fixture.create_database_table(database=database, order=2)
    table_2 = data_fixture.create_database_table(database=database, order=1)
    data_fixture.create_database_table(database=database_2)

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 2
    assert response_json[0]["id"] == table_2.id
    assert response_json[1]["id"] == table_1.id

    url = reverse("api:database:tables:list", kwargs={"database_id": database_2.id})
    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:tables:list", kwargs={"database_id": 9999})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_APPLICATION_DOES_NOT_EXIST"

    response = api_client.delete(
        reverse("api:groups:item", kwargs={"group_id": database.group.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_APPLICATION_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_list_tables_doesnt_do_n_queries_per_tables(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    database_2 = data_fixture.create_database_application()
    table_1 = data_fixture.create_database_table(database=database, order=2)
    table_2 = data_fixture.create_database_table(database=database, order=1)
    data_fixture.create_database_table(database=database_2)

    with CaptureQueriesContext(connection) as query_for_n_tables:
        url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
        response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
        assert response.status_code == HTTP_200_OK

    table_3 = data_fixture.create_database_table(database=database, order=1)

    with CaptureQueriesContext(connection) as query_for_n_plus_one_tables:
        url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
        response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
        assert response.status_code == HTTP_200_OK

    assert len(query_for_n_tables.captured_queries) == len(
        query_for_n_plus_one_tables.captured_queries
    )


@pytest.mark.django_db
def test_create_table(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    database_2 = data_fixture.create_database_application()

    url = reverse(
        "api:database:tables:async_create", kwargs={"database_id": database_2.id}
    )
    response = api_client.post(
        url, {"name": "Test 1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse(
        "api:database:tables:async_create", kwargs={"database_id": database.id}
    )
    response = api_client.post(
        url, {"not_a_name": "Test 1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    url = reverse("api:database:tables:async_create", kwargs={"database_id": 9999})
    response = api_client.post(
        url, {"name": "Test 1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_APPLICATION_DOES_NOT_EXIST"

    # Should create an example database
    url = reverse(
        "api:database:tables:async_create", kwargs={"database_id": database.id}
    )
    response = api_client.post(
        url, {"name": "Test 1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    json_response = response.json()

    job = FileImportJob.objects.get(id=json_response["id"])

    assert job.table is not None
    assert job.table.name == "Test 1"

    model = job.table.get_model()

    assert job.table.field_set.count() == 3
    assert model.objects.count() == 2


@pytest.mark.django_db(transaction=True)
@patch("baserow.core.jobs.handler.run_async_job")
def test_create_table_with_data(
    mock_run_async_job, api_client, data_fixture, patch_filefield_storage
):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    url = reverse(
        "api:database:tables:async_create", kwargs={"database_id": database.id}
    )

    response = api_client.post(
        url,
        {"name": "Test 1", "data": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["data"][0]["code"] == "min_length"

    with patch_filefield_storage():
        response = api_client.post(
            url,
            {
                "name": "Test 1",
                "data": [
                    ["A", "B", "C", "D"],
                    ["1-1", "1-2", "1-3", "1-4", "1-5"],
                    ["2-1", "2-2", "2-3"],
                    ["3-1", "3-2"],
                ],
                "first_row_header": True,
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    mock_run_async_job.delay.assert_called_with(response_json["id"])

    job = FileImportJob.objects.get(id=response_json["id"])

    assert job.table is None
    assert job.name == "Test 1"
    assert job.first_row_header
    assert job.database == database

    with patch_filefield_storage():
        with job.data_file.open("r") as fin:
            data = json.load(fin)
            assert data == [
                ["A", "B", "C", "D"],
                ["1-1", "1-2", "1-3", "1-4", "1-5"],
                ["2-1", "2-2", "2-3"],
                ["3-1", "3-2"],
            ]


@pytest.mark.django_db(transaction=True)
def test_create_table_with_data_sync(api_client, data_fixture, patch_filefield_storage):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})

    with override_settings(
        BASEROW_INITIAL_CREATE_SYNC_TABLE_DATA_LIMIT=2
    ), patch_filefield_storage():
        response = api_client.post(
            url,
            {
                "name": "Test 1",
                "data": [
                    ["A", "B", "C", "D"],
                    ["1-1", "1-2", "1-3", "1-4", "1-5"],
                    ["2-1", "2-2", "2-3"],
                    ["3-1", "3-2"],
                ],
                "first_row_header": True,
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_INITIAL_SYNC_TABLE_DATA_LIMIT_EXCEEDED"

    with patch_filefield_storage():
        response = api_client.post(
            url,
            {
                "name": "Test 1",
                "data": [
                    ["A", "B", "C", "D"],
                    ["1-1", "1-2", "1-3", "1-4", "1-5"],
                    ["2-1", "2-2", "2-3"],
                    ["3-1", "3-2"],
                ],
                "first_row_header": True,
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert response_json["name"] == "Test 1"

    table = Table.objects.get(id=response_json["id"])

    model = table.get_model()
    assert model.objects.count() == 3

    # Test empty data
    with patch_filefield_storage():
        response = api_client.post(
            url,
            {
                "name": "Test 2",
                "first_row_header": True,
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert response_json["name"] == "Test 2"

    table = Table.objects.get(id=response_json["id"])

    model = table.get_model()
    assert model.objects.count() == 2


@pytest.mark.django_db
def test_get_table(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()

    url = reverse("api:database:tables:item", kwargs={"table_id": table_1.id})
    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_200_OK
    json_response = response.json()
    assert json_response["id"] == table_1.id
    assert json_response["name"] == table_1.name
    assert json_response["order"] == table_1.order
    assert json_response["database_id"] == table_1.database_id

    url = reverse("api:database:tables:item", kwargs={"table_id": table_2.id})
    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
    json_response = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert json_response["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:tables:item", kwargs={"table_id": 9999})
    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_update_table(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()

    url = reverse("api:database:tables:item", kwargs={"table_id": table_1.id})
    response = api_client.patch(
        url, {"name": "New name"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    table_1.refresh_from_db()

    assert response_json["id"] == table_1.id
    assert response_json["name"] == table_1.name == "New name"

    url = reverse("api:database:tables:item", kwargs={"table_id": table_2.id})
    response = api_client.patch(
        url, {"name": "New name"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:tables:item", kwargs={"table_id": table_1.id})
    response = api_client.patch(
        url,
        {"not_a_name": "New name"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    url = reverse("api:database:tables:item", kwargs={"table_id": 999})
    response = api_client.patch(
        url, {"name": "New name"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_order_tables(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    database_1 = data_fixture.create_database_application(user=user)
    database_2 = data_fixture.create_database_application()
    table_1 = data_fixture.create_database_table(database=database_1, order=1)
    table_2 = data_fixture.create_database_table(database=database_1, order=2)
    table_3 = data_fixture.create_database_table(database=database_1, order=3)

    response = api_client.post(
        reverse("api:database:tables:order", kwargs={"database_id": database_2.id}),
        {"table_ids": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.post(
        reverse("api:database:tables:order", kwargs={"database_id": 999999}),
        {"table_ids": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_APPLICATION_DOES_NOT_EXIST"

    response = api_client.post(
        reverse("api:database:tables:order", kwargs={"database_id": database_1.id}),
        {"table_ids": [0]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_TABLE_NOT_IN_DATABASE"

    response = api_client.post(
        reverse("api:database:tables:order", kwargs={"database_id": database_1.id}),
        {"table_ids": ["test"]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    response = api_client.post(
        reverse("api:database:tables:order", kwargs={"database_id": database_1.id}),
        {"table_ids": [table_3.id, table_2.id, table_1.id]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT

    table_1.refresh_from_db()
    table_2.refresh_from_db()
    table_3.refresh_from_db()
    assert table_1.order == 3
    assert table_2.order == 2
    assert table_3.order == 1


@pytest.mark.django_db
def test_delete_table(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()

    assert Table.objects.all().count() == 2
    url = reverse("api:database:tables:item", kwargs={"table_id": table_1.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == 204
    assert Table.objects.all().count() == 1

    url = reverse("api:database:tables:item", kwargs={"table_id": table_2.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:tables:item", kwargs={"table_id": 9999})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_get_database_application_with_tables(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    table_1 = data_fixture.create_database_table(database=database, order=0)
    table_2 = data_fixture.create_database_table(database=database, order=1)
    data_fixture.create_database_table()

    url = reverse("api:applications:item", kwargs={"application_id": database.id})
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["tables"]) == 2
    assert response_json["tables"][0]["id"] == table_1.id
    assert response_json["tables"][1]["id"] == table_2.id


@pytest.mark.django_db(transaction=True)
def test_update_table_returns_with_error_if_cant_lock_table_if_locked_for_update(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)

    with independent_test_db_connection() as conn:
        with conn.cursor() as cursor:
            # nosec
            cursor.execute(
                f"SELECT * FROM database_table where id = {table.id} FOR UPDATE"
            )
            response = api_client.patch(
                reverse("api:database:tables:item", kwargs={"table_id": table.id}),
                {"name": "Test 1"},
                format="json",
                HTTP_AUTHORIZATION=f"JWT {token}",
            )
    response_json = response.json()
    assert response.status_code == HTTP_409_CONFLICT
    assert response_json["error"] == "ERROR_FAILED_TO_LOCK_TABLE_DUE_TO_CONFLICT"


@pytest.mark.django_db(transaction=True)
def test_update_table_returns_with_error_if_cant_lock_table_if_locked_for_share(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)

    with independent_test_db_connection() as conn:
        with conn.cursor() as cursor:
            # nosec
            cursor.execute(
                f"SELECT * FROM database_table where id = {table.id} FOR SHARE"
            )
            response = api_client.patch(
                reverse("api:database:tables:item", kwargs={"table_id": table.id}),
                {"name": "Test 1"},
                format="json",
                HTTP_AUTHORIZATION=f"JWT {token}",
            )
    response_json = response.json()
    assert response.status_code == HTTP_409_CONFLICT
    assert response_json["error"] == "ERROR_FAILED_TO_LOCK_TABLE_DUE_TO_CONFLICT"


@pytest.mark.django_db(transaction=True)
def test_delete_table_returns_with_error_if_cant_lock_table_if_locked_for_update(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)

    with independent_test_db_connection() as conn:
        with conn.cursor() as cursor:
            # nosec
            cursor.execute(
                f"SELECT * FROM database_table where id = {table.id} FOR UPDATE"
            )
            response = api_client.delete(
                reverse("api:database:tables:item", kwargs={"table_id": table.id}),
                format="json",
                HTTP_AUTHORIZATION=f"JWT {token}",
            )
    response_json = response.json()
    assert response.status_code == HTTP_409_CONFLICT
    assert response_json["error"] == "ERROR_FAILED_TO_LOCK_TABLE_DUE_TO_CONFLICT"


@pytest.mark.django_db(transaction=True)
def test_delete_table_returns_with_error_if_cant_lock_table_if_locked_for_share(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)

    with independent_test_db_connection() as conn:
        with conn.cursor() as cursor:
            # nosec
            cursor.execute(
                f"SELECT * FROM database_table where id = {table.id} FOR SHARE"
            )
            response = api_client.delete(
                reverse("api:database:tables:item", kwargs={"table_id": table.id}),
                format="json",
                HTTP_AUTHORIZATION=f"JWT {token}",
            )
    response_json = response.json()
    assert response.status_code == HTTP_409_CONFLICT
    assert response_json["error"] == "ERROR_FAILED_TO_LOCK_TABLE_DUE_TO_CONFLICT"

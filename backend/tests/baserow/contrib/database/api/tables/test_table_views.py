import pytest

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from django.shortcuts import reverse
from django.conf import settings

from baserow.contrib.database.fields.models import TextField
from baserow.contrib.database.table.models import Table


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
def test_create_table(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    database_2 = data_fixture.create_database_application()

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url, {"name": "Test 1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    json_response = response.json()

    Table.objects.all().count() == 1
    table = Table.objects.filter(database=database).first()

    assert table.order == json_response["order"] == 1
    assert table.name == json_response["name"]
    assert table.id == json_response["id"]

    url = reverse("api:database:tables:list", kwargs={"database_id": database_2.id})
    response = api_client.post(
        url, {"name": "Test 1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url, {"not_a_name": "Test 1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    url = reverse("api:database:tables:list", kwargs={"database_id": 9999})
    response = api_client.post(
        url, {"name": "Test 1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_APPLICATION_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_create_table_with_data(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
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

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url,
        {"name": "Test 1", "data": [[]]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_INVALID_INITIAL_TABLE_DATA"

    limit = settings.INITIAL_TABLE_DATA_LIMIT
    settings.INITIAL_TABLE_DATA_LIMIT = 2
    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url,
        {"name": "Test 1", "data": [[], [], []]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_INITIAL_TABLE_DATA_LIMIT_EXCEEDED"
    settings.INITIAL_TABLE_DATA_LIMIT = limit

    field_limit = settings.MAX_FIELD_LIMIT
    settings.MAX_FIELD_LIMIT = 2
    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url,
        {"name": "Test 1", "data": [["fields"] * 3, ["rows"] * 3]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_MAX_FIELD_COUNT_EXCEEDED"
    settings.MAX_FIELD_LIMIT = field_limit

    too_long_field_name = "x" * 256
    field_name_with_ok_length = "x" * 255

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url,
        {
            "name": "Test 1",
            "data": [
                [too_long_field_name, "B", "C", "D"],
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
    assert response_json["error"] == "ERROR_MAX_FIELD_NAME_LENGTH_EXCEEDED"

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url,
        {
            "name": "Test 1",
            "data": [
                [field_name_with_ok_length, "B", "C", "D"],
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

    table = Table.objects.get(id=response_json["id"])

    text_fields = TextField.objects.filter(table=table)
    assert text_fields[0].name == field_name_with_ok_length
    assert text_fields[1].name == "B"
    assert text_fields[2].name == "C"
    assert text_fields[3].name == "D"
    assert text_fields[4].name == "Field 5"

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
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

    table = Table.objects.get(id=response_json["id"])

    text_fields = TextField.objects.filter(table=table)
    assert text_fields[0].name == "A"
    assert text_fields[1].name == "B"
    assert text_fields[2].name == "C"
    assert text_fields[3].name == "D"
    assert text_fields[4].name == "Field 5"

    model = table.get_model()
    results = model.objects.all()

    assert results.count() == 3

    assert getattr(results[0], f"field_{text_fields[0].id}") == "1-1"
    assert getattr(results[0], f"field_{text_fields[1].id}") == "1-2"
    assert getattr(results[0], f"field_{text_fields[2].id}") == "1-3"
    assert getattr(results[0], f"field_{text_fields[3].id}") == "1-4"
    assert getattr(results[0], f"field_{text_fields[4].id}") == "1-5"

    assert getattr(results[1], f"field_{text_fields[0].id}") == "2-1"
    assert getattr(results[1], f"field_{text_fields[1].id}") == "2-2"
    assert getattr(results[1], f"field_{text_fields[2].id}") == "2-3"
    assert getattr(results[1], f"field_{text_fields[3].id}") == ""
    assert getattr(results[1], f"field_{text_fields[4].id}") == ""

    assert getattr(results[2], f"field_{text_fields[0].id}") == "3-1"
    assert getattr(results[2], f"field_{text_fields[1].id}") == "3-2"
    assert getattr(results[2], f"field_{text_fields[2].id}") == ""
    assert getattr(results[2], f"field_{text_fields[3].id}") == ""
    assert getattr(results[2], f"field_{text_fields[4].id}") == ""

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url,
        {
            "name": "Test 2",
            "data": [
                ["1-1"],
                ["2-1", "2-2", "2-3"],
                ["3-1", "3-2"],
            ],
            "first_row_header": False,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    table = Table.objects.get(id=response_json["id"])

    text_fields = TextField.objects.filter(table=table)
    assert text_fields[0].name == "Field 1"
    assert text_fields[1].name == "Field 2"
    assert text_fields[2].name == "Field 3"

    model = table.get_model()
    results = model.objects.all()

    assert results.count() == 3

    assert getattr(results[0], f"field_{text_fields[0].id}") == "1-1"
    assert getattr(results[0], f"field_{text_fields[1].id}") == ""
    assert getattr(results[0], f"field_{text_fields[2].id}") == ""

    assert getattr(results[1], f"field_{text_fields[0].id}") == "2-1"
    assert getattr(results[1], f"field_{text_fields[1].id}") == "2-2"
    assert getattr(results[1], f"field_{text_fields[2].id}") == "2-3"

    assert getattr(results[2], f"field_{text_fields[0].id}") == "3-1"
    assert getattr(results[2], f"field_{text_fields[1].id}") == "3-2"

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url,
        {
            "name": "Test 2",
            "data": [
                [
                    "TEst 1",
                    "10.00",
                    'Falsea"""',
                    'a"a"a"a"a,',
                    "a",
                    "/w. r/awr",
                ],
            ],
            "first_row_header": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    table = Table.objects.get(id=response_json["id"])
    text_fields = TextField.objects.filter(table=table)
    assert text_fields[0].name == "TEst 1"
    assert text_fields[1].name == "10.00"
    assert text_fields[2].name == 'Falsea"""'
    assert text_fields[3].name == 'a"a"a"a"a,'
    assert text_fields[4].name == "a"
    assert text_fields[5].name == "/w. r/awr"

    model = table.get_model()
    results = model.objects.all()
    assert results.count() == 0

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url,
        {
            "name": "Test 4",
            "data": [
                [
                    "id",
                ],
            ],
            "first_row_header": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_RESERVED_BASEROW_FIELD_NAME"

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url,
        {
            "name": "Test 4",
            "data": [
                [
                    "test",
                    "test",
                ],
            ],
            "first_row_header": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_INITIAL_TABLE_DATA_HAS_DUPLICATE_NAMES"
    assert "unique" in response_json["detail"]

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url,
        {
            "name": "Test 4",
            "data": [
                [
                    " ",
                ],
            ],
            "first_row_header": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_INVALID_BASEROW_FIELD_NAME"
    assert "blank" in response_json["detail"]

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.post(
        url,
        {
            "name": "Test 4",
            "data": [
                [
                    " test 1",
                    "  test 2",
                ],
            ],
            "first_row_header": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK


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

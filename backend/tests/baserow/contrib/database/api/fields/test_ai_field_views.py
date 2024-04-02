from unittest.mock import patch

from django.conf import settings
from django.shortcuts import reverse

import pytest
from rest_framework.status import (
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
@pytest.mark.field_ai
def test_generate_ai_field_value_view_field_does_not_exist(data_fixture, api_client):
    data_fixture.register_fake_generate_ai_type()
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    database = data_fixture.create_database_application(user=user, name="database")
    table = data_fixture.create_database_table(name="table", database=database)
    field = data_fixture.create_ai_field(table=table, name="ai")

    rows = RowHandler().create_rows(
        user,
        table,
        rows_values=[{}],
    )

    response = api_client.post(
        reverse(
            "api:database:fields:async_generate_ai_field_values",
            kwargs={"field_id": 0},
        ),
        {"row_ids": [rows[0].id]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FIELD_DOES_NOT_EXIST"


@pytest.mark.django_db
@pytest.mark.field_ai
def test_generate_ai_field_value_view_row_does_not_exist(data_fixture, api_client):
    data_fixture.register_fake_generate_ai_type()
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    database = data_fixture.create_database_application(user=user, name="database")
    table = data_fixture.create_database_table(name="table", database=database)
    field = data_fixture.create_ai_field(table=table, name="ai")

    rows = RowHandler().create_rows(
        user,
        table,
        rows_values=[{}],
    )

    response = api_client.post(
        reverse(
            "api:database:fields:async_generate_ai_field_values",
            kwargs={"field_id": field.id},
        ),
        {"row_ids": [0]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ROW_DOES_NOT_EXIST"


@pytest.mark.django_db
@pytest.mark.field_ai
def test_generate_ai_field_value_view_user_not_in_workspace(data_fixture, api_client):
    data_fixture.register_fake_generate_ai_type()
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    user_2, token_2 = data_fixture.create_user_and_token(
        email="test2@test.nl", password="password", first_name="Test1"
    )

    database = data_fixture.create_database_application(user=user, name="database")
    table = data_fixture.create_database_table(name="table", database=database)
    field = data_fixture.create_ai_field(table=table, name="ai")

    rows = RowHandler().create_rows(
        user,
        table,
        rows_values=[{}],
    )

    response = api_client.post(
        reverse(
            "api:database:fields:async_generate_ai_field_values",
            kwargs={"field_id": field.id},
        ),
        {"row_ids": [rows[0].id]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"


@pytest.mark.django_db
@pytest.mark.field_ai
def test_generate_ai_field_value_view_generative_ai_does_not_exist(
    data_fixture, api_client
):
    data_fixture.register_fake_generate_ai_type()
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    database = data_fixture.create_database_application(user=user, name="database")
    table = data_fixture.create_database_table(name="table", database=database)
    field = data_fixture.create_ai_field(
        table=table, name="ai", ai_generative_ai_type="does_not_exist"
    )

    rows = RowHandler().create_rows(
        user,
        table,
        rows_values=[{}],
    )

    response = api_client.post(
        reverse(
            "api:database:fields:async_generate_ai_field_values",
            kwargs={"field_id": field.id},
        ),
        {"row_ids": [rows[0].id]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_GENERATIVE_AI_DOES_NOT_EXIST"


@pytest.mark.django_db
@pytest.mark.field_ai
def test_generate_ai_field_value_view_generative_ai_model_does_not_belong_to_type(
    data_fixture, api_client
):
    data_fixture.register_fake_generate_ai_type()
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    database = data_fixture.create_database_application(user=user, name="database")
    table = data_fixture.create_database_table(name="table", database=database)
    field = data_fixture.create_ai_field(
        table=table, name="ai", ai_generative_ai_model="does_not_exist"
    )

    rows = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {},
        ],
    )

    response = api_client.post(
        reverse(
            "api:database:fields:async_generate_ai_field_values",
            kwargs={"field_id": field.id},
        ),
        {"row_ids": [rows[0].id]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_MODEL_DOES_NOT_BELONG_TO_TYPE"


@pytest.mark.django_db
@pytest.mark.field_ai
@patch("baserow.contrib.database.fields.tasks.generate_ai_values_for_rows.apply")
def test_generate_ai_field_value_view_generative_ai(
    patched_generate_ai_values_for_rows, data_fixture, api_client
):
    data_fixture.register_fake_generate_ai_type()
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    database = data_fixture.create_database_application(user=user, name="database")
    table = data_fixture.create_database_table(name="table", database=database)
    field = data_fixture.create_ai_field(table=table, name="ai", ai_prompt="'Hello'")

    rows = RowHandler().create_rows(
        user,
        table,
        rows_values=[{}],
    )
    assert patched_generate_ai_values_for_rows.call_count == 0

    response = api_client.post(
        reverse(
            "api:database:fields:async_generate_ai_field_values",
            kwargs={"field_id": field.id},
        ),
        {"row_ids": [rows[0].id]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_202_ACCEPTED
    assert patched_generate_ai_values_for_rows.call_count == 1


@pytest.mark.django_db
@pytest.mark.field_ai
def test_batch_generate_ai_field_value_limit(api_client, data_fixture):
    data_fixture.register_fake_generate_ai_type()
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_ai_field(table=table, name="ai", ai_prompt="'Hello'")
    rows = RowHandler().create_rows(
        user,
        table,
        rows_values=[{}] * (settings.BATCH_ROWS_SIZE_LIMIT + 1),
    )

    row_ids = [row.id for row in rows]

    # BATCH_ROWS_SIZE_LIMIT rows are allowed
    response = api_client.post(
        reverse(
            "api:database:fields:async_generate_ai_field_values",
            kwargs={"field_id": field.id},
        ),
        {"row_ids": row_ids[: settings.BATCH_ROWS_SIZE_LIMIT]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_202_ACCEPTED

    # BATCH_ROWS_SIZE_LIMIT + 1 rows are not allowed
    response = api_client.post(
        reverse(
            "api:database:fields:async_generate_ai_field_values",
            kwargs={"field_id": field.id},
        ),
        {"row_ids": row_ids},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"] == {
        "row_ids": [
            {
                "code": "max_length",
                "error": f"Ensure this field has no more than"
                f" {settings.BATCH_ROWS_SIZE_LIMIT} elements.",
            },
        ],
    }

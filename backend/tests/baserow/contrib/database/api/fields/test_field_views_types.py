from datetime import date, datetime
from decimal import Decimal

import pytest
from django.shortcuts import reverse
from faker import Faker
from freezegun import freeze_time
from pytz import timezone
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from baserow.contrib.database.fields.models import (
    LongTextField,
    URLField,
    DateField,
    EmailField,
    FileField,
    NumberField,
    PhoneNumberField,
)


@pytest.mark.django_db
def test_text_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(
        table=table, order=0, name="Old name", text_default="Default"
    )

    response = api_client.patch(
        reverse("api:database:fields:item", kwargs={"field_id": text_field.id}),
        {"name": "New name"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["text_default"] == "Default"


@pytest.mark.django_db
def test_long_text_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    fake = Faker()
    text = fake.text()

    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "Long text", "type": "long_text"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "long_text"
    assert LongTextField.objects.all().count() == 1
    field_id = response_json["id"]

    response = api_client.patch(
        reverse("api:database:fields:item", kwargs={"field_id": field_id}),
        {"name": "Long text 2"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": text},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == text

    model = table.get_model(attribute_names=True)
    row = model.objects.all().last()
    assert row.long_text_2 == text

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": ""},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == ""

    row = model.objects.all().last()
    assert row.long_text_2 == ""

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": None},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] is None

    row = model.objects.all().last()
    assert row.long_text_2 is None

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] is None

    row = model.objects.all().last()
    assert row.long_text_2 is None

    url = reverse("api:database:fields:item", kwargs={"field_id": field_id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT
    assert LongTextField.objects.all().count() == 0


@pytest.mark.django_db
def test_url_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)

    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "URL", "type": "url"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "url"
    assert URLField.objects.all().count() == 1
    field_id = response_json["id"]

    response = api_client.patch(
        reverse("api:database:fields:item", kwargs={"field_id": field_id}),
        {"name": "URL2"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": "https://test.nl"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == "https://test.nl"

    model = table.get_model(attribute_names=True)
    row = model.objects.all().last()
    assert row.url2 == "https://test.nl"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": ""},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == ""

    row = model.objects.all().last()
    assert row.url2 == ""

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": None},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == ""

    row = model.objects.all().last()
    assert row.url2 == ""

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == ""

    row = model.objects.all().last()
    assert row.url2 == ""

    url = reverse("api:database:fields:item", kwargs={"field_id": field_id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT
    assert URLField.objects.all().count() == 0


@pytest.mark.django_db
def test_date_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)

    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "Date", "type": "date"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "date"
    assert DateField.objects.all().count() == 1
    date_field_id = response_json["id"]

    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "Datetime", "type": "date", "date_include_time": True},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "date"
    assert DateField.objects.all().count() == 2
    date_time_field_id = response_json["id"]

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{date_field_id}": "2020-04-01 12:00",
            f"field_{date_time_field_id}": "2020-04-01",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"][f"field_{date_field_id}"][0]["code"] == "invalid"
    assert response_json["detail"][f"field_{date_time_field_id}"][0]["code"] == (
        "invalid"
    )

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{date_field_id}": "2020-04-01",
            f"field_{date_time_field_id}": "2020-04-01 14:30:20",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{date_field_id}"] == "2020-04-01"
    assert response_json[f"field_{date_time_field_id}"] == "2020-04-01T14:30:20Z"

    model = table.get_model(attribute_names=True)
    row = model.objects.all().last()
    assert row.date == date(2020, 4, 1)
    assert row.datetime == datetime(2020, 4, 1, 14, 30, 20, tzinfo=timezone("UTC"))

    url = reverse("api:database:fields:item", kwargs={"field_id": date_time_field_id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT
    assert DateField.objects.all().count() == 1


@pytest.mark.django_db
def test_email_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)

    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "Email", "type": "email"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "email"
    assert EmailField.objects.all().count() == 1
    field_id = response_json["id"]

    response = api_client.patch(
        reverse("api:database:fields:item", kwargs={"field_id": field_id}),
        {"name": "Email2"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": "test@test.nl"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == "test@test.nl"

    model = table.get_model(attribute_names=True)
    row = model.objects.all().last()
    assert row.email2 == "test@test.nl"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": ""},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == ""

    row = model.objects.all().last()
    assert row.email2 == ""

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": None},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == ""

    row = model.objects.all().last()
    assert row.email2 == ""

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == ""

    row = model.objects.all().last()
    assert row.email2 == ""

    email = reverse("api:database:fields:item", kwargs={"field_id": field_id})
    response = api_client.delete(email, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT
    assert EmailField.objects.all().count() == 0


@pytest.mark.django_db
def test_file_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    grid = data_fixture.create_grid_view(table=table)
    with freeze_time("2020-01-01 12:00"):
        user_file_1 = data_fixture.create_user_file(
            original_name="test.txt",
            original_extension="txt",
            unique="sdafi6WtHfnDrU6S1lQKh9PdC7PeafCA",
            size=10,
            mime_type="text/plain",
            is_image=True,
            image_width=1920,
            image_height=1080,
            sha256_hash=(
                "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
            ),
        )

    user_file_2 = data_fixture.create_user_file()
    user_file_3 = data_fixture.create_user_file()

    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "File", "type": "file"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "file"
    assert FileField.objects.all().count() == 1
    field_id = response_json["id"]

    response = api_client.patch(
        reverse("api:database:fields:item", kwargs={"field_id": field_id}),
        {"name": "File2"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == []

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == []

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": [{"without_name": "test"}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": [{"name": "an__invalid__name.jpg"}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response_json["detail"][f"field_{field_id}"][0]["name"][0]["code"] == "invalid"
    )

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": [{"name": "not_existing.jpg"}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_FILE_DOES_NOT_EXIST"
    assert response_json["detail"] == "The user file not_existing.jpg does not exist."

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": [{"name": user_file_1.name, "is_image": True}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()

    assert response.status_code == HTTP_200_OK
    assert (
        response_json[f"field_{field_id}"][0]["visible_name"]
        == user_file_1.original_name
    )
    assert response_json[f"field_{field_id}"][0]["name"] == (
        "sdafi6WtHfnDrU6S1lQKh9PdC7PeafCA_"
        "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e.txt"
    )
    assert response_json[f"field_{field_id}"][0]["size"] == 10
    assert response_json[f"field_{field_id}"][0]["mime_type"] == "text/plain"
    assert response_json[f"field_{field_id}"][0]["is_image"] is True
    assert response_json[f"field_{field_id}"][0]["image_width"] == 1920
    assert response_json[f"field_{field_id}"][0]["image_height"] == 1080
    assert response_json[f"field_{field_id}"][0]["uploaded_at"] == (
        "2020-01-01T12:00:00+00:00"
    )
    assert "localhost:8000" in response_json[f"field_{field_id}"][0]["url"]
    assert len(response_json[f"field_{field_id}"][0]["thumbnails"]) == 1
    assert (
        "localhost:8000"
        in response_json[f"field_{field_id}"][0]["thumbnails"]["tiny"]["url"]
    )
    assert (
        "sdafi6WtHfnDrU6S1lQKh9PdC7PeafCA_"
        "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e.txt"
        in response_json[f"field_{field_id}"][0]["thumbnails"]["tiny"]["url"]
    )
    assert "tiny" in response_json[f"field_{field_id}"][0]["thumbnails"]["tiny"]["url"]
    assert response_json[f"field_{field_id}"][0]["thumbnails"]["tiny"]["width"] == 21
    assert response_json[f"field_{field_id}"][0]["thumbnails"]["tiny"]["height"] == 21
    assert "original_name" not in response_json
    assert "original_extension" not in response_json
    assert "sha256_hash" not in response_json

    response = api_client.patch(
        reverse(
            "api:database:rows:item",
            kwargs={"table_id": table.id, "row_id": response_json["id"]},
        ),
        {
            f"field_{field_id}": [
                {"name": user_file_3.name},
                {"name": user_file_2.name, "visible_name": "new_name_1.txt"},
            ]
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json[f"field_{field_id}"][0]["name"] == user_file_3.name
    assert (
        response_json[f"field_{field_id}"][0]["visible_name"]
        == user_file_3.original_name
    )
    assert "localhost:8000" in response_json[f"field_{field_id}"][0]["url"]
    assert response_json[f"field_{field_id}"][0]["is_image"] is False
    assert response_json[f"field_{field_id}"][0]["image_width"] is None
    assert response_json[f"field_{field_id}"][0]["image_height"] is None
    assert response_json[f"field_{field_id}"][0]["thumbnails"] is None
    assert response_json[f"field_{field_id}"][1]["name"] == user_file_2.name
    assert response_json[f"field_{field_id}"][1]["visible_name"] == "new_name_1.txt"

    response = api_client.patch(
        reverse(
            "api:database:rows:item",
            kwargs={"table_id": table.id, "row_id": response_json["id"]},
        ),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.get(
        reverse(
            "api:database:rows:item",
            kwargs={"table_id": table.id, "row_id": response_json["id"]},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json[f"field_{field_id}"][0]["name"] == user_file_3.name
    assert (
        response_json[f"field_{field_id}"][0]["visible_name"]
        == user_file_3.original_name
    )
    assert "localhost:8000" in response_json[f"field_{field_id}"][0]["url"]
    assert response_json[f"field_{field_id}"][1]["name"] == user_file_2.name
    assert response_json[f"field_{field_id}"][1]["visible_name"] == "new_name_1.txt"

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json["results"]) == 3
    assert response_json["results"][0][f"field_{field_id}"] == []
    assert response_json["results"][1][f"field_{field_id}"] == []
    assert (
        response_json["results"][2][f"field_{field_id}"][0]["name"] == user_file_3.name
    )
    assert (
        "localhost:8000" in response_json["results"][2][f"field_{field_id}"][0]["url"]
    )
    assert (
        response_json["results"][2][f"field_{field_id}"][1]["name"] == user_file_2.name
    )

    # We also need to check if the grid view returns the correct url because the
    # request context must be provided there in order to work.
    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json["results"]) == 3
    assert response_json["results"][0][f"field_{field_id}"] == []
    assert response_json["results"][1][f"field_{field_id}"] == []
    assert (
        response_json["results"][2][f"field_{field_id}"][0]["name"] == user_file_3.name
    )
    assert (
        "localhost:8000" in response_json["results"][2][f"field_{field_id}"][0]["url"]
    )
    assert (
        response_json["results"][2][f"field_{field_id}"][1]["name"] == user_file_2.name
    )


@pytest.mark.django_db
def test_number_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)

    # Create a positive integer field
    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {
            "name": "PositiveInt",
            "type": "number",
            "number_type": "INTEGER",
            "number_negative": False,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    # Make sure the field was created properly
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "number"
    assert NumberField.objects.all().count() == 1
    positive_int_field_id = response_json["id"]

    # Create a negative integer field
    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {
            "name": "NegativeInt",
            "type": "number",
            "number_type": "INTEGER",
            "number_negative": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    # Make sure the field was created properly
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "number"
    assert NumberField.objects.all().count() == 2
    negative_int_field_id = response_json["id"]

    # Create a positive decimal field
    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {
            "name": "PositiveDecimal",
            "type": "number",
            "number_type": "DECIMAL",
            "number_negative": False,
            "number_decimal_places": 2,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    # Make sure the field was created properly
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "number"
    assert NumberField.objects.all().count() == 3
    positive_decimal_field_id = response_json["id"]

    # Create a negative decimal field
    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {
            "name": "NegativeDecimal",
            "type": "number",
            "number_type": "DECIMAL",
            "number_negative": True,
            "number_decimal_places": 2,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    # Make sure the field was created properly
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "number"
    assert NumberField.objects.all().count() == 4
    negative_decimal_field_id = response_json["id"]

    # Test re-writing the name of a field. 'PositiveInt' is now called 'PositiveIntEdit'
    response = api_client.patch(
        reverse("api:database:fields:item", kwargs={"field_id": positive_int_field_id}),
        {"name": "PositiveIntEdit"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    # Add a row with correct values
    valid_pos_int = "99999999999999999999999999999999999999999999999999"
    valid_neg_int = "-99999999999999999999999999999999999999999999999999"
    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{positive_int_field_id}": valid_pos_int,
            f"field_{negative_int_field_id}": valid_neg_int,
            f"field_{positive_decimal_field_id}": 1000.00,
            f"field_{negative_decimal_field_id}": -1000.00,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{positive_int_field_id}"] == valid_pos_int
    assert response_json[f"field_{negative_int_field_id}"] == valid_neg_int
    assert response_json[f"field_{positive_decimal_field_id}"] == "1000.00"
    assert response_json[f"field_{negative_decimal_field_id}"] == "-1000.00"

    model = table.get_model(attribute_names=True)
    row = model.objects.all().last()
    assert row.positiveintedit == Decimal(valid_pos_int)
    assert row.negativeint == Decimal(valid_neg_int)
    assert row.positivedecimal == Decimal(1000.00)
    assert row.negativedecimal == Decimal(-1000.00)

    # Add a row with Nones'
    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{positive_int_field_id}": None,
            f"field_{negative_int_field_id}": None,
            f"field_{positive_decimal_field_id}": None,
            f"field_{negative_decimal_field_id}": None,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{positive_int_field_id}"] is None
    assert response_json[f"field_{negative_int_field_id}"] is None
    assert response_json[f"field_{positive_decimal_field_id}"] is None
    assert response_json[f"field_{negative_decimal_field_id}"] is None

    row = model.objects.all().last()
    assert row.positiveintedit is None
    assert row.negativeint is None
    assert row.positivedecimal is None
    assert row.negativedecimal is None

    # Add a row with an integer that's too big
    invalid_pos_int = "999999999999999999999999999999999999999999999999999"
    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{positive_int_field_id}": invalid_pos_int,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response_json["detail"][f"field_{positive_int_field_id}"][0]["code"]
        == "max_digits"
    )

    # Add a row with an integer that's too small
    invalid_neg_int = "-9999999999999999999999999999999999999999999999999999"
    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{negative_int_field_id}": invalid_neg_int,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response_json["detail"][f"field_{positive_int_field_id}"][0]["code"]
        == "max_digits"
    )


@pytest.mark.django_db
def test_phone_number_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)

    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "phone", "type": "phone_number"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "phone_number"
    assert PhoneNumberField.objects.all().count() == 1
    field_id = response_json["id"]

    response = api_client.patch(
        reverse("api:database:fields:item", kwargs={"field_id": field_id}),
        {"name": "Phone"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    expected_phone_number = "+44761198672"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": expected_phone_number},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == expected_phone_number

    model = table.get_model(attribute_names=True)
    row = model.objects.all().last()
    assert row.phone == expected_phone_number

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": ""},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == ""

    row = model.objects.all().last()
    assert row.phone == ""

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{field_id}": None},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == ""

    row = model.objects.all().last()
    assert row.phone == ""

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{field_id}"] == ""

    row = model.objects.all().last()
    assert row.phone == ""

    email = reverse("api:database:fields:item", kwargs={"field_id": field_id})
    response = api_client.delete(email, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT
    assert PhoneNumberField.objects.all().count() == 0

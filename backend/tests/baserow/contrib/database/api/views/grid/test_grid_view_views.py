from typing import List, Dict, Any

import pytest
from django.shortcuts import reverse
from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.rows.registries import (
    RowMetadataType,
    row_metadata_registry,
)
from baserow.contrib.database.views.models import GridView
from baserow.core.trash.handler import TrashHandler
from baserow.test_utils.helpers import register_instance_temporarily


@pytest.mark.django_db
def test_list_rows(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(
        table=table, order=0, name="Color", text_default="white"
    )
    number_field = data_fixture.create_number_field(
        table=table, order=1, name="Horsepower"
    )
    boolean_field = data_fixture.create_boolean_field(
        table=table, order=2, name="For sale"
    )
    grid = data_fixture.create_grid_view(table=table)
    grid_2 = data_fixture.create_grid_view()

    model = grid.table.get_model()
    row_1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Green",
            f"field_{number_field.id}": 10,
            f"field_{boolean_field.id}": False,
        }
    )
    row_2 = model.objects.create()
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": "Orange",
            f"field_{number_field.id}": 100,
            f"field_{boolean_field.id}": True,
        }
    )
    row_4 = model.objects.create(
        **{
            f"field_{text_field.id}": "Purple",
            f"field_{number_field.id}": 1000,
            f"field_{boolean_field.id}": False,
        }
    )

    url = reverse("api:database:views:grid:list", kwargs={"view_id": 999})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GRID_DOES_NOT_EXIST"

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid_2.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert not response_json["previous"]
    assert not response_json["next"]
    assert len(response_json["results"]) == 4
    assert response_json["results"][0]["id"] == row_1.id
    assert response_json["results"][0][f"field_{text_field.id}"] == "Green"
    assert response_json["results"][0][f"field_{number_field.id}"] == "10"
    assert not response_json["results"][0][f"field_{boolean_field.id}"]
    assert response_json["results"][1]["id"] == row_2.id
    assert response_json["results"][2]["id"] == row_3.id
    assert response_json["results"][3]["id"] == row_4.id

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(
        url, {"size": 2}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert not response_json["previous"]
    assert response_json["next"]
    assert len(response_json["results"]) == 2
    assert response_json["results"][0]["id"] == row_1.id
    assert response_json["results"][1]["id"] == row_2.id

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(
        url, {"size": 2, "page": 2}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert response_json["previous"]
    assert not response_json["next"]
    assert len(response_json["results"]) == 2
    assert response_json["results"][0]["id"] == row_3.id
    assert response_json["results"][1]["id"] == row_4.id

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(
        url, {"size": 2, "page": 999}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_INVALID_PAGE"

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(
        url, {"limit": 2}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert response_json["results"][0]["id"] == row_1.id
    assert response_json["results"][1]["id"] == row_2.id
    assert "field_options" not in response_json

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(
        url, {"limit": 1, "offset": 2}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert response_json["results"][0]["id"] == row_3.id

    sort = data_fixture.create_view_sort(view=grid, field=text_field, order="ASC")
    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert response_json["results"][0]["id"] == row_1.id
    assert response_json["results"][1]["id"] == row_3.id
    assert response_json["results"][2]["id"] == row_4.id
    assert response_json["results"][3]["id"] == row_2.id
    sort.delete()

    view_filter = data_fixture.create_view_filter(
        view=grid, field=text_field, value="Green"
    )
    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_1.id
    view_filter.delete()

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(
        url, data={"count": ""}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response_json["count"] == 4
    assert len(response_json.keys()) == 1

    row_1.delete()
    row_2.delete()
    row_3.delete()
    row_4.delete()

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 0
    assert not response_json["previous"]
    assert not response_json["next"]
    assert len(response_json["results"]) == 0

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(url)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    data_fixture.create_template(group=grid.table.database.group)
    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(url)
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_list_rows_include_field_options(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(
        table=table, order=0, name="Color", text_default="white"
    )
    grid = data_fixture.create_grid_view(table=table)

    # The second field is deliberately created after the creation of the grid field
    # so that the GridViewFieldOptions entry is not created. This should
    # automatically be created when the page is fetched.
    number_field = data_fixture.create_number_field(
        table=table, order=1, name="Horsepower"
    )

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert "field_options" not in response_json

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(
        url, {"include": "field_options"}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["field_options"]) == 2
    assert response_json["field_options"][str(text_field.id)]["width"] == 200
    assert response_json["field_options"][str(text_field.id)]["hidden"] is False
    assert response_json["field_options"][str(text_field.id)]["order"] == 32767
    assert response_json["field_options"][str(number_field.id)]["width"] == 200
    assert response_json["field_options"][str(number_field.id)]["hidden"] is False
    assert response_json["field_options"][str(number_field.id)]["order"] == 32767
    assert "filters_disabled" not in response_json


@pytest.mark.django_db
def test_list_rows_include_row_metadata(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(
        name="test", table=table, order=0, text_default="white"
    )
    grid = data_fixture.create_grid_view(table=table)
    model = table.get_model(attribute_names=True)
    row = model.objects.create(test="test")

    class ExampleRowMetadata(RowMetadataType):
        type = "test_example_row_metadata"

        def generate_metadata_for_rows(
            self, table, row_ids: List[int]
        ) -> Dict[int, Any]:
            return {row_id: row_id for row_id in row_ids}

        def get_example_serializer_field(self) -> Field:
            return serializers.CharField()

    with register_instance_temporarily(row_metadata_registry, ExampleRowMetadata()):
        url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
        response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
        response_json = response.json()
        assert response.status_code == HTTP_200_OK
        assert "row_metadata" not in response_json

        url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
        response = api_client.get(
            url, {"include": "row_metadata"}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
        )
        response_json = response.json()
        assert response.status_code == HTTP_200_OK
        assert response_json["row_metadata"] == {
            str(row.id): {"test_example_row_metadata": row.id}
        }


@pytest.mark.django_db
def test_list_filtered_rows(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(
        table=table, order=0, name="Color", text_default="white"
    )
    number_field = data_fixture.create_number_field(
        table=table, order=1, name="Horsepower"
    )
    boolean_field = data_fixture.create_boolean_field(
        table=table, order=2, name="For sale"
    )
    grid = data_fixture.create_grid_view(table=table)
    grid_2 = data_fixture.create_grid_view()

    url = reverse("api:database:views:grid:list", kwargs={"view_id": 999})
    response = api_client.post(
        url,
        {"field_ids": [1], "row_ids": [1]},
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GRID_DOES_NOT_EXIST"

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid_2.id})
    response = api_client.post(
        url,
        {"field_ids": [1], "row_ids": [1]},
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.post(url, {}, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(url)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.post(
        url,
        {"field_ids": ["a", "b"], "row_ids": ["a", "b"]},
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert len(response_json["detail"]["field_ids"]) == 2
    assert len(response_json["detail"]["row_ids"]) == 2

    model = grid.table.get_model()
    row_1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Green",
            f"field_{number_field.id}": 10,
            f"field_{boolean_field.id}": False,
        }
    )
    row_2 = model.objects.create()
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": "Orange",
            f"field_{number_field.id}": 100,
            f"field_{boolean_field.id}": True,
        }
    )
    model.objects.create(
        **{
            f"field_{text_field.id}": "Purple",
            f"field_{number_field.id}": 1000,
            f"field_{boolean_field.id}": False,
        }
    )

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.post(
        url,
        {"field_ids": [text_field.id], "row_ids": [row_1.id, row_2.id]},
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert len(response_json) == 2
    assert response_json[0]["id"] == row_1.id
    assert f"field_{text_field.id}" in response_json[0]
    assert response_json[1]["id"] == row_2.id
    assert f"field_{text_field.id}" in response_json[1]

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.post(
        url,
        {"field_ids": [number_field.id, boolean_field.id], "row_ids": [row_3.id]},
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert len(response_json) == 1
    assert response_json[0]["id"] == row_3.id
    assert f"field_{number_field.id}" in response_json[0]
    assert f"field_{boolean_field.id}" in response_json[0]

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.post(
        url, {"row_ids": [row_3.id]}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert len(response_json) == 1
    assert response_json[0]["id"] == row_3.id
    assert f"field_{text_field.id}" in response_json[0]
    assert f"field_{number_field.id}" in response_json[0]
    assert f"field_{boolean_field.id}" in response_json[0]


@pytest.mark.django_db
def test_patch_grid_view_field_options(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    data_fixture.create_text_field()
    grid = data_fixture.create_grid_view(table=table)
    # The second field is deliberately created after the creation of the grid field
    # so that the GridViewFieldOptions entry is not created. This should
    # automatically be created when the page is fetched.
    number_field = data_fixture.create_number_field(table=table)

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url,
        {"field_options": {text_field.id: {"width": 300, "hidden": True}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["field_options"]) == 2
    assert response_json["field_options"][str(text_field.id)]["width"] == 300
    assert response_json["field_options"][str(text_field.id)]["hidden"] is True
    assert response_json["field_options"][str(text_field.id)]["order"] == 32767
    assert response_json["field_options"][str(number_field.id)]["width"] == 200
    assert response_json["field_options"][str(number_field.id)]["hidden"] is False
    assert response_json["field_options"][str(number_field.id)]["order"] == 32767
    options = grid.get_field_options()
    assert len(options) == 2
    assert options[0].field_id == text_field.id
    assert options[0].width == 300
    assert options[0].hidden is True
    assert options[0].order == 32767
    assert options[1].field_id == number_field.id
    assert options[1].width == 200
    assert options[1].hidden is False
    assert options[1].order == 32767

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url,
        {
            "field_options": {
                text_field.id: {"width": 100, "hidden": False},
                number_field.id: {"width": 500, "hidden": True},
            }
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["field_options"]) == 2
    assert response_json["field_options"][str(text_field.id)]["width"] == 100
    assert response_json["field_options"][str(text_field.id)]["hidden"] is False
    assert response_json["field_options"][str(number_field.id)]["width"] == 500
    assert response_json["field_options"][str(number_field.id)]["hidden"] is True
    options = grid.get_field_options()
    assert len(options) == 2
    assert options[0].field_id == text_field.id
    assert options[0].width == 100
    assert options[0].hidden is False
    assert options[1].field_id == number_field.id
    assert options[1].hidden is True

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url,
        {
            "field_options": {
                text_field.id: {
                    "width": 200,
                },
                number_field.id: {
                    "hidden": False,
                },
            }
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["field_options"]) == 2
    assert response_json["field_options"][str(text_field.id)]["width"] == 200
    assert response_json["field_options"][str(text_field.id)]["hidden"] is False
    assert response_json["field_options"][str(number_field.id)]["width"] == 500
    assert response_json["field_options"][str(number_field.id)]["hidden"] is False
    options = grid.get_field_options()
    assert len(options) == 2
    assert options[0].field_id == text_field.id
    assert options[0].width == 200
    assert options[0].hidden is False
    assert options[1].field_id == number_field.id
    assert options[1].hidden is False

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url, {"field_options": {}}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url,
        {"field_options": {"RANDOM_FIELD": "TEST"}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["field_options"][0]["code"] == "invalid_key"

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url,
        {"field_options": {1: {"width": "abc"}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["field_options"][0]["code"] == "invalid_value"

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url,
        {"field_options": {1: {"hidden": "abc"}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["field_options"][0]["code"] == "invalid_value"


@pytest.mark.django_db
def test_create_grid_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {"name": "Test 1", "type": "NOT_EXISTING"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["type"][0]["code"] == "invalid_choice"

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": 99999}),
        {"name": "Test 1", "type": "grid"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table_2.id}),
        {"name": "Test 1", "type": "grid"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:views:list", kwargs={"table_id": table_2.id})
    response = api_client.get(url)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "name": "Test 1",
            "type": "grid",
            "filter_type": "OR",
            "filters_disabled": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "grid"
    assert response_json["filter_type"] == "OR"
    assert response_json["filters_disabled"] is True

    grid = GridView.objects.filter()[0]
    assert response_json["id"] == grid.id
    assert response_json["name"] == grid.name
    assert response_json["order"] == grid.order
    assert response_json["filter_type"] == grid.filter_type
    assert response_json["filters_disabled"] == grid.filters_disabled
    assert "filters" not in response_json
    assert "sortings" not in response_json

    response = api_client.post(
        "{}?include=filters,sortings".format(
            reverse("api:database:views:list", kwargs={"table_id": table.id})
        ),
        {
            "name": "Test 2",
            "type": "grid",
            "filter_type": "AND",
            "filters_disabled": False,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Test 2"
    assert response_json["type"] == "grid"
    assert response_json["filter_type"] == "AND"
    assert response_json["filters_disabled"] is False
    assert response_json["filters"] == []
    assert response_json["sortings"] == []

    response = api_client.post(
        "{}".format(reverse("api:database:views:list", kwargs={"table_id": table.id})),
        {"name": "Test 3", "type": "grid"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Test 3"
    assert response_json["type"] == "grid"
    assert response_json["filter_type"] == "AND"
    assert response_json["filters_disabled"] is False
    assert "filters" not in response_json
    assert "sortings" not in response_json

    # Can't create a public non sharable view.
    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {"name": "Test 1", "type": "gallery", "public": True},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert "public" not in response_json
    assert "slug" not in response_json


@pytest.mark.django_db
def test_update_grid_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user_2)
    view = data_fixture.create_grid_view(table=table)
    view_2 = data_fixture.create_grid_view(table=table_2)
    not_sharable_view = data_fixture.create_gallery_view(table=table)

    url = reverse("api:database:views:item", kwargs={"view_id": view_2.id})
    response = api_client.patch(
        url, {"name": "Test 1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:views:item", kwargs={"view_id": 999999})
    response = api_client.patch(
        url, {"name": "Test 1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.patch(
        url,
        {"UNKNOWN_FIELD": "Test 1"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.patch(
        url, {"name": "Test 1"}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == view.id
    assert response_json["name"] == "Test 1"
    assert response_json["filter_type"] == "AND"
    assert not response_json["filters_disabled"]

    view.refresh_from_db()
    assert view.name == "Test 1"
    assert view.filter_type == "AND"
    assert not view.filters_disabled

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.patch(
        url,
        {
            "filter_type": "OR",
            "filters_disabled": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == view.id
    assert response_json["filter_type"] == "OR"
    assert response_json["filters_disabled"]
    assert "filters" not in response_json
    assert "sortings" not in response_json

    view.refresh_from_db()
    assert view.filter_type == "OR"
    assert view.filters_disabled

    filter_1 = data_fixture.create_view_filter(view=view)
    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.patch(
        "{}?include=filters,sortings".format(url),
        {"filter_type": "AND"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == view.id
    assert response_json["filter_type"] == "AND"
    assert response_json["filters_disabled"] is True
    assert response_json["filters"][0]["id"] == filter_1.id
    assert response_json["sortings"] == []

    # Can't make a non sharable view public.
    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": not_sharable_view.id}),
        {"public": True},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK, response_json
    assert "public" not in response_json
    assert "slug" not in response_json


@pytest.mark.django_db
def test_get_public_grid_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)

    # Only information related the public field should be returned
    public_field = data_fixture.create_text_field(table=table, name="public")
    hidden_field = data_fixture.create_text_field(table=table, name="hidden")

    grid_view = data_fixture.create_grid_view(
        table=table, user=user, public=True, create_options=False
    )

    data_fixture.create_grid_view_field_option(grid_view, public_field, hidden=False)
    data_fixture.create_grid_view_field_option(grid_view, hidden_field, hidden=True)

    # This view sort shouldn't be exposed as it is for a hidden field
    data_fixture.create_view_sort(view=grid_view, field=hidden_field, order="ASC")
    visible_sort = data_fixture.create_view_sort(
        view=grid_view, field=public_field, order="DESC"
    )

    # View filters should not be returned at all for any and all fields regardless of
    # if they are hidden.
    data_fixture.create_view_filter(
        view=grid_view, field=hidden_field, type="contains", value="hidden"
    )
    data_fixture.create_view_filter(
        view=grid_view, field=public_field, type="contains", value="public"
    )

    # Can access as an anonymous user
    response = api_client.get(
        reverse("api:database:views:grid:public_info", kwargs={"slug": grid_view.slug})
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK, response_json
    assert response_json == {
        "fields": [
            {
                "id": public_field.id,
                "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                "name": "public",
                "order": 0,
                "primary": False,
                "text_default": "",
                "type": "text",
            }
        ],
        "view": {
            "id": grid_view.slug,
            "name": grid_view.name,
            "order": 0,
            "public": True,
            "slug": grid_view.slug,
            "sortings": [
                # Note the sorting for the hidden field is not returned
                {
                    "field": visible_sort.field.id,
                    "id": visible_sort.id,
                    "order": "DESC",
                    "view": grid_view.slug,
                }
            ],
            "table": {
                "database_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                "id": PUBLIC_PLACEHOLDER_ENTITY_ID,
            },
            "type": "grid",
        },
    }


@pytest.mark.django_db
def test_anon_user_cant_get_info_about_a_non_public_grid_view(api_client, data_fixture):
    user = data_fixture.create_user()
    grid_view = data_fixture.create_grid_view(user=user, public=False)

    # Get access as an anonymous user
    response = api_client.get(
        reverse("api:database:views:grid:public_info", kwargs={"slug": grid_view.slug})
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json == {
        "detail": "The requested view does not exist.",
        "error": "ERROR_VIEW_DOES_NOT_EXIST",
    }


@pytest.mark.django_db
def test_user_in_wrong_group_cant_get_info_about_a_non_public_grid_view(
    api_client, data_fixture
):
    user = data_fixture.create_user()
    other_user, other_user_token = data_fixture.create_user_and_token()
    grid_view = data_fixture.create_grid_view(user=user, public=False)

    response = api_client.get(
        reverse(
            "api:database:views:grid:public_info",
            kwargs={"slug": grid_view.slug},
        ),
        HTTP_AUTHORIZATION=f"JWT {other_user_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json == {
        "detail": "The requested view does not exist.",
        "error": "ERROR_VIEW_DOES_NOT_EXIST",
    }


@pytest.mark.django_db
def test_user_in_same_group_can_get_info_about_a_non_public_grid_view(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    grid_view = data_fixture.create_grid_view(user=user, public=False)

    response = api_client.get(
        reverse(
            "api:database:views:grid:public_info",
            kwargs={"slug": grid_view.slug},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK, response_json
    assert "fields" in response_json
    assert "view" in response_json


@pytest.mark.django_db
def test_cannot_get_info_about_non_grid_view(api_client, data_fixture):
    user = data_fixture.create_user()
    form_view = data_fixture.create_form_view(user=user, public=True)

    # Get access as an anonymous user
    response = api_client.get(
        reverse(
            "api:database:views:grid:public_info",
            kwargs={"slug": form_view.slug},
        ),
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json == {
        "detail": "The requested view does not exist.",
        "error": "ERROR_VIEW_DOES_NOT_EXIST",
    }


@pytest.mark.django_db
def test_cannot_get_info_about_trashed_grid_view(api_client, data_fixture):
    user = data_fixture.create_user()
    grid_view = data_fixture.create_grid_view(user=user, public=True)

    TrashHandler.trash(
        user, grid_view.table.database.group, None, grid_view.table.database.group
    )

    response = api_client.get(
        reverse(
            "api:database:views:grid:public_info",
            kwargs={"slug": grid_view.slug},
        ),
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json == {
        "detail": "The requested view does not exist.",
        "error": "ERROR_VIEW_DOES_NOT_EXIST",
    }


@pytest.mark.django_db
def test_list_rows_public_doesnt_show_hidden_columns(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)

    # Only information related the public field should be returned
    public_field = data_fixture.create_text_field(table=table, name="public")
    hidden_field = data_fixture.create_text_field(table=table, name="hidden")

    grid_view = data_fixture.create_grid_view(
        table=table, user=user, public=True, create_options=False
    )

    public_field_option = data_fixture.create_grid_view_field_option(
        grid_view, public_field, hidden=False
    )
    data_fixture.create_grid_view_field_option(grid_view, hidden_field, hidden=True)

    RowHandler().create_row(user, table, values={})

    # Get access as an anonymous user
    response = api_client.get(
        reverse("api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug})
        + "?include=field_options"
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                f"field_{public_field.id}": None,
                "id": 1,
                "order": "1.00000000000000000000",
            }
        ],
        "field_options": {
            f"{public_field.id}": {
                "hidden": False,
                "order": public_field_option.order,
                "width": public_field_option.width,
            },
        },
    }


@pytest.mark.django_db
def test_list_rows_public_doesnt_sort_by_hidden_columns(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)

    # Only information related the public field should be returned
    public_field = data_fixture.create_text_field(table=table, name="public")
    hidden_field = data_fixture.create_text_field(table=table, name="hidden")

    grid_view = data_fixture.create_grid_view(
        table=table, user=user, public=True, create_options=False
    )

    data_fixture.create_grid_view_field_option(grid_view, public_field, hidden=False)
    data_fixture.create_grid_view_field_option(grid_view, hidden_field, hidden=True)

    second_row = RowHandler().create_row(
        user, table, values={"public": "a", "hidden": "y"}, user_field_names=True
    )
    first_row = RowHandler().create_row(
        user, table, values={"public": "b", "hidden": "z"}, user_field_names=True
    )

    data_fixture.create_view_sort(view=grid_view, field=hidden_field, order="ASC")
    data_fixture.create_view_sort(view=grid_view, field=public_field, order="DESC")

    # Get access as an anonymous user
    response = api_client.get(
        reverse("api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug})
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK, response_json
    assert response_json["results"][0]["id"] == first_row.id
    assert response_json["results"][1]["id"] == second_row.id


@pytest.mark.django_db
def test_list_rows_public_filters_by_visible_and_hidden_columns(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)

    # Only information related the public field should be returned
    public_field = data_fixture.create_text_field(table=table, name="public")
    hidden_field = data_fixture.create_text_field(table=table, name="hidden")

    grid_view = data_fixture.create_grid_view(
        table=table, user=user, public=True, create_options=False
    )

    data_fixture.create_grid_view_field_option(grid_view, public_field, hidden=False)
    data_fixture.create_grid_view_field_option(grid_view, hidden_field, hidden=True)

    data_fixture.create_view_filter(
        view=grid_view, field=hidden_field, type="equal", value="y"
    )
    data_fixture.create_view_filter(
        view=grid_view, field=public_field, type="equal", value="a"
    )
    # A row whose hidden column doesn't match the first filter
    RowHandler().create_row(
        user, table, values={"public": "a", "hidden": "not y"}, user_field_names=True
    )
    # A row whose public column doesn't match the second filter
    RowHandler().create_row(
        user, table, values={"public": "not a", "hidden": "y"}, user_field_names=True
    )
    # A row which matches all filters
    visible_row = RowHandler().create_row(
        user, table, values={"public": "a", "hidden": "y"}, user_field_names=True
    )

    # Get access as an anonymous user
    response = api_client.get(
        reverse("api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug})
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK, response_json
    assert len(response_json["results"]) == 1
    assert response_json["count"] == 1
    assert response_json["results"][0]["id"] == visible_row.id


@pytest.mark.django_db
def test_list_rows_public_only_searches_by_visible_columns(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)

    # Only information related the public field should be returned
    public_field = data_fixture.create_text_field(table=table, name="public")
    hidden_field = data_fixture.create_text_field(table=table, name="hidden")

    grid_view = data_fixture.create_grid_view(
        table=table, user=user, public=True, create_options=False
    )

    data_fixture.create_grid_view_field_option(grid_view, public_field, hidden=False)
    data_fixture.create_grid_view_field_option(grid_view, hidden_field, hidden=True)

    search_term = "search_term"
    RowHandler().create_row(
        user,
        table,
        values={"public": "other", "hidden": search_term},
        user_field_names=True,
    )
    RowHandler().create_row(
        user,
        table,
        values={"public": "other", "hidden": "other"},
        user_field_names=True,
    )
    visible_row = RowHandler().create_row(
        user,
        table,
        values={"public": search_term, "hidden": "other"},
        user_field_names=True,
    )

    # Get access as an anonymous user
    response = api_client.get(
        reverse("api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug})
        + f"?search={search_term}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK, response_json
    assert len(response_json["results"]) == 1
    assert response_json["count"] == 1
    assert response_json["results"][0]["id"] == visible_row.id

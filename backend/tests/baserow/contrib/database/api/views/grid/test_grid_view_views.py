from decimal import Decimal
from typing import Any, Dict, List

from django.core.cache import cache
from django.shortcuts import reverse

import pytest
from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.rows.registries import (
    RowMetadataType,
    row_metadata_registry,
)
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import GridView
from baserow.contrib.database.views.registries import view_aggregation_type_registry
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
def test_field_aggregation(api_client, data_fixture):
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

    table2 = data_fixture.create_database_table(user=user)
    text_field2 = data_fixture.create_text_field(
        table=table2, order=0, name="Color", text_default="white"
    )

    # Test missing grid view
    url = reverse(
        "api:database:views:grid:field-aggregation",
        kwargs={"view_id": 9999, "field_id": text_field.id},
    )
    response = api_client.get(
        url + f"?type=empty_count",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GRID_DOES_NOT_EXIST"

    # Test aggregation on missing field
    url = reverse(
        "api:database:views:grid:field-aggregation",
        kwargs={"view_id": grid.id, "field_id": 9999},
    )
    response = api_client.get(
        url + f"?type=empty_count",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FIELD_DOES_NOT_EXIST"

    # Test user not authorized
    url = reverse(
        "api:database:views:grid:field-aggregation",
        kwargs={"view_id": grid_2.id, "field_id": text_field.id},
    )
    response = api_client.get(
        url + f"?type=empty_count",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    # Test field not in table
    url = reverse(
        "api:database:views:grid:field-aggregation",
        kwargs={"view_id": grid.id, "field_id": text_field2.id},
    )
    response = api_client.get(
        url + f"?type=empty_count",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_FIELD_NOT_IN_TABLE"

    # Test missing auth token
    url = reverse(
        "api:database:views:grid:field-aggregation",
        kwargs={"view_id": grid.id, "field_id": text_field.id},
    )
    response = api_client.get(url)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    url = reverse(
        "api:database:views:grid:field-aggregation",
        kwargs={"view_id": grid.id, "field_id": text_field.id},
    )

    # Test bad aggregation type
    response = api_client.get(
        url + f"?type=bad_aggregation_type",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_AGGREGATION_TYPE_DOES_NOT_EXIST"

    # Test normal response with no data
    response = api_client.get(
        url + f"?type=empty_count",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert response_json == {f"value": 0}

    # Add more data
    model = grid.table.get_model()
    model.objects.create(
        **{
            f"field_{text_field.id}": "Green",
            f"field_{number_field.id}": 10,
            f"field_{boolean_field.id}": False,
        }
    )
    model.objects.create()
    model.objects.create(
        **{
            f"field_{text_field.id}": "",
            f"field_{number_field.id}": 0,
            f"field_{boolean_field.id}": False,
        }
    )

    model.objects.create(
        **{
            f"field_{text_field.id}": None,
            f"field_{number_field.id}": 1200,
            f"field_{boolean_field.id}": True,
        }
    )

    # Count empty boolean field
    response = api_client.get(
        url + f"?type=empty_count",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert response_json == {f"value": 2}

    url = reverse(
        "api:database:views:grid:field-aggregation",
        kwargs={"view_id": grid.id, "field_id": boolean_field.id},
    )

    # Count not empty "For sale" field
    response = api_client.get(
        url + f"?type=not_empty_count",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert response_json == {
        "value": 1,
    }

    # Count with total
    response = api_client.get(
        url + f"?type=not_empty_count&include=total",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert response_json == {"value": 1, "total": 4}

    # Does it work with filter
    data_fixture.create_view_filter(
        view=grid, field=number_field, type="higher_than", value="10"
    )

    # Count with total
    response = api_client.get(
        url + f"?type=not_empty_count",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert response_json == {"value": 1}


@pytest.mark.django_db
def test_view_aggregations(api_client, data_fixture):
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

    # Test missing grid view
    url = reverse(
        "api:database:views:grid:field-aggregations",
        kwargs={"view_id": 9999},
    )
    response = api_client.get(
        url,
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GRID_DOES_NOT_EXIST"

    # Test user not authorized
    url = reverse(
        "api:database:views:grid:field-aggregations",
        kwargs={"view_id": grid_2.id},
    )
    response = api_client.get(
        url + f"?type=empty_count",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    # Test missing auth token
    url = reverse(
        "api:database:views:grid:field-aggregations",
        kwargs={"view_id": grid.id},
    )
    response = api_client.get(url)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    url = reverse(
        "api:database:views:grid:field-aggregations",
        kwargs={"view_id": grid.id},
    )

    # Test normal response with no data and no aggregation
    response = api_client.get(
        url,
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert response_json == {}

    field_option1 = data_fixture.create_grid_view_field_option(
        grid_view=grid,
        field=text_field,
        aggregation_type="",
        aggregation_raw_type="",
    )

    field_option2 = data_fixture.create_grid_view_field_option(
        grid_view=grid,
        field=number_field,
        aggregation_type="whatever",
        aggregation_raw_type="sum",
    )

    field_option3 = data_fixture.create_grid_view_field_option(
        grid_view=grid,
        field=boolean_field,
        aggregation_type="whatever",
        aggregation_raw_type="empty_count",
    )

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") is None
    assert cache.get(f"aggregation_version__{grid.id}_{number_field.db_column}") is None
    assert cache.get(f"aggregation_value__{grid.id}_{boolean_field.db_column}") is None
    assert (
        cache.get(f"aggregation_version__{grid.id}_{boolean_field.db_column}") is None
    )

    # Test normal response with no data and no cache
    response = api_client.get(
        url,
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert response_json == {number_field.db_column: None, boolean_field.db_column: 0}

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": None,
        "version": 1,
    }
    assert cache.get(f"aggregation_version__{grid.id}_{number_field.db_column}") is None
    assert cache.get(f"aggregation_value__{grid.id}_{boolean_field.db_column}") == {
        "value": 0,
        "version": 1,
    }
    assert (
        cache.get(f"aggregation_version__{grid.id}_{boolean_field.db_column}") is None
    )

    # Test normal response that use cache
    cache.set(
        f"aggregation_value__{grid.id}_{number_field.db_column}",
        {"value": "sentinel", "version": 1},
    )
    cache.set(
        f"aggregation_value__{grid.id}_{boolean_field.db_column}",
        {"value": "sentinel", "version": 1},
    )

    response = api_client.get(
        url,
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert response_json == {
        number_field.db_column: "sentinel",
        boolean_field.db_column: "sentinel",
    }

    cache.set(
        f"aggregation_value__{grid.id}_{number_field.db_column}",
        {"value": "sentinel", "version": 1},
    )
    cache.set(
        f"aggregation_value__{grid.id}_{boolean_field.db_column}",
        {"value": "sentinel", "version": 3},
    )
    cache.set(
        f"aggregation_version__{grid.id}_{boolean_field.db_column}",
        3,
    )

    # Add data through the API to trigger cache update
    api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{text_field.id}": "Green",
            f"field_{number_field.id}": 10,
            f"field_{boolean_field.id}": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": "sentinel",
        "version": 1,
    }
    assert cache.get(f"aggregation_version__{grid.id}_{number_field.db_column}") == 2
    assert cache.get(f"aggregation_value__{grid.id}_{boolean_field.db_column}") == {
        "value": "sentinel",
        "version": 3,
    }
    assert cache.get(f"aggregation_version__{grid.id}_{boolean_field.db_column}") == 4

    api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{text_field.id}": "",
            f"field_{number_field.id}": 0,
            f"field_{boolean_field.id}": False,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{text_field.id}": None,
            f"field_{number_field.id}": 1200,
            f"field_{boolean_field.id}": False,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    # Test normal response with data
    response = api_client.get(
        url,
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert response_json == {number_field.db_column: 1210.0, boolean_field.db_column: 2}

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": 1210.0,
        "version": 4,
    }
    assert cache.get(f"aggregation_version__{grid.id}_{number_field.db_column}") == 4
    assert cache.get(f"aggregation_value__{grid.id}_{boolean_field.db_column}") == {
        "value": 2,
        "version": 6,
    }
    assert cache.get(f"aggregation_version__{grid.id}_{boolean_field.db_column}") == 6

    # with total
    response = api_client.get(
        url + f"?include=total",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert response_json == {
        number_field.db_column: 1210.0,
        boolean_field.db_column: 2,
        "total": 3,
    }

    # Does it work with filter
    response = api_client.get(
        url + f"?include=total&search=GREE",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert response_json == {
        number_field.db_column: 10.0,
        boolean_field.db_column: 0,
        "total": 1,
    }

    # But cache shouldn't be modified after a search as we don't use the cache
    assert cache.get(f"aggregation_version__{grid.id}_{number_field.db_column}") == 4
    assert cache.get(f"aggregation_version__{grid.id}_{boolean_field.db_column}") == 6

    # Does it work with filter (use API to trigger cache update)
    response = api_client.post(
        reverse("api:database:views:list_filters", kwargs={"view_id": grid.id}),
        {"field": number_field.id, "type": "higher_than", "value": "10"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    filter_id = response.json()["id"]

    # Cache should be invalidated on filter creation
    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": Decimal(1210),
        "version": 4,
    }
    assert cache.get(f"aggregation_value__{grid.id}_{boolean_field.db_column}") == {
        "value": 2,
        "version": 6,
    }
    assert cache.get(f"aggregation_version__{grid.id}_{number_field.db_column}") == 5
    assert cache.get(f"aggregation_version__{grid.id}_{boolean_field.db_column}") == 7

    response = api_client.get(
        url + f"?include=total",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert response_json == {
        number_field.db_column: 1200.0,
        boolean_field.db_column: 1,
        "total": 1,
    }

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": Decimal(1200),
        "version": 5,
    }
    assert cache.get(f"aggregation_value__{grid.id}_{boolean_field.db_column}") == {
        "value": 1,
        "version": 7,
    }

    # Let's update the filter
    api_client.patch(
        reverse("api:database:views:filter_item", kwargs={"view_filter_id": filter_id}),
        {"value": 5},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert cache.get(f"aggregation_version__{grid.id}_{number_field.db_column}") == 6
    assert cache.get(f"aggregation_version__{grid.id}_{boolean_field.db_column}") == 8

    response = api_client.get(
        url + f"?include=total",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert response_json == {
        number_field.db_column: 1210.0,
        boolean_field.db_column: 1,
        "total": 2,
    }

    # Cache should also be invalidated on filter deletion
    api_client.delete(
        reverse("api:database:views:filter_item", kwargs={"view_filter_id": filter_id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert cache.get(f"aggregation_version__{grid.id}_{number_field.db_column}") == 7
    assert cache.get(f"aggregation_version__{grid.id}_{boolean_field.db_column}") == 9

    response = api_client.get(
        url + f"?include=total",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert response_json == {
        number_field.db_column: 1210.0,
        boolean_field.db_column: 2,
        "total": 3,
    }


@pytest.mark.django_db
def test_view_aggregations_cache_invalidation_with_dependant_fields(
    api_client, data_fixture
):
    """
    Here we want a complex situation where we need to invalidate the cache of a
    dependant field in another table. Should be the more extreme scenario.
    We create two tables with a link row field from table2 to table1, a lookup field on
    table 2 to the number field on table 1 and a formula that sum the values of
    table 2's lookup field.
    """

    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    table2 = data_fixture.create_database_table(user=user, database=table.database)
    number_field = data_fixture.create_number_field(
        table=table, order=1, name="Horsepower"
    )
    grid = data_fixture.create_grid_view(table=table)
    grid2 = data_fixture.create_grid_view(table=table2)

    linkrowfield = FieldHandler().create_field(
        user,
        table2,
        "link_row",
        name="linkrowfield",
        link_row_table=table,
    )

    lookup_field = FieldHandler().create_field(
        user,
        table2,
        "lookup",
        name="lookup_field",
        through_field_id=linkrowfield.id,
        target_field_id=number_field.id,
    )

    sum_formula_on_lookup_field = FieldHandler().create_field(
        user,
        table2,
        "formula",
        name="sum",
        formula='sum(field("lookup_field"))',
    )

    # Create some aggregations
    data_fixture.create_grid_view_field_option(
        grid_view=grid,
        field=number_field,
        aggregation_type="whatever",
        aggregation_raw_type="sum",
    )

    data_fixture.create_grid_view_field_option(
        grid_view=grid2,
        field=sum_formula_on_lookup_field,
        aggregation_type="whatever",
        aggregation_raw_type="sum",
    )

    # Define some utilities functions
    def add_value_to_table1(value):
        # Add data through the API to trigger cache update
        response = api_client.post(
            reverse("api:database:rows:list", kwargs={"table_id": table.id}),
            {
                f"field_{number_field.id}": value,
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        return response.json()

    def update_value_of_table1(row, value):
        api_client.patch(
            reverse(
                "api:database:rows:item",
                kwargs={"table_id": table.id, "row_id": row["id"]},
            ),
            {f"field_{number_field.id}": value},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    def delete_row_of_table1(row):
        api_client.delete(
            reverse(
                "api:database:rows:item",
                kwargs={"table_id": table.id, "row_id": row["id"]},
            ),
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    def add_link_to_table2(links):
        # Add data through the API to trigger cache update
        response = api_client.post(
            reverse("api:database:rows:list", kwargs={"table_id": table2.id}),
            {
                f"field_{linkrowfield.id}": [link["id"] for link in links],
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        return response.json()

    def check_table_2_aggregation_values(value_to_check, ident):
        response = api_client.get(
            url2,
            **{"HTTP_AUTHORIZATION": f"JWT {token}"},
        )
        response_json = response.json()

        assert response_json == value_to_check, ident

    url = reverse(
        "api:database:views:grid:field-aggregations",
        kwargs={"view_id": grid.id},
    )
    url2 = reverse(
        "api:database:views:grid:field-aggregations",
        kwargs={"view_id": grid2.id},
    )

    row1 = add_value_to_table1(1)
    row2 = add_value_to_table1(10)
    row3 = add_value_to_table1(100)
    row4 = add_value_to_table1(1000)

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") is None
    assert (
        cache.get(
            f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
        )
        is None
    )

    api_client.get(
        url,
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": Decimal(1111),
        "version": 5,
    }
    assert (
        cache.get(
            f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
        )
        is None
    )

    check_table_2_aggregation_values(
        {sum_formula_on_lookup_field.db_column: None}, "with no link"
    )

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": Decimal(1111),
        "version": 5,
    }
    assert cache.get(
        f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
    ) == {"value": None, "version": 5}

    cache.set(
        f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}",
        {"value": "sentinel", "version": 0},
    )

    # Add few links
    add_link_to_table2([row1, row2])

    assert cache.get(
        f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
    ) == {"value": "sentinel", "version": 0}

    add_link_to_table2([row2, row3])
    add_link_to_table2([row3, row4])
    add_link_to_table2([row4])

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": Decimal(1111),
        "version": 5,
    }

    check_table_2_aggregation_values(
        {sum_formula_on_lookup_field.db_column: 2221}, "after link addition"
    )

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": Decimal(1111),
        "version": 5,
    }
    assert cache.get(
        f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
    ) == {
        "value": Decimal(2221),
        "version": 13,
    }

    update_value_of_table1(row2, 10000)

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": Decimal(1111),
        "version": 5,
    }
    assert cache.get(f"aggregation_version__{grid.id}_{number_field.db_column}") == 6
    assert cache.get(
        f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
    ) == {
        "value": Decimal(2221),
        "version": 13,
    }
    assert (
        cache.get(
            f"aggregation_version__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
        )
        == 14
    )

    check_table_2_aggregation_values(
        {sum_formula_on_lookup_field.db_column: 22201}, "after table 1 value update"
    )

    # Delete row3 from table1
    api_client.delete(
        reverse(
            "api:database:rows:item",
            kwargs={"table_id": table.id, "row_id": row3["id"]},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": Decimal("1111"),
        "version": 5,
    }
    assert cache.get(f"aggregation_version__{grid.id}_{number_field.db_column}") == 7

    # Should increment cache version
    assert (
        cache.get(
            f"aggregation_version__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
        )
        == 15
    )

    check_table_2_aggregation_values(
        {sum_formula_on_lookup_field.db_column: 22001}, "after row deletion"
    )

    assert cache.get(f"aggregation_value__{grid.id}_{number_field.db_column}") == {
        "value": Decimal("1111"),
        "version": 5,
    }
    assert cache.get(f"aggregation_version__{grid.id}_{number_field.db_column}") == 7
    assert cache.get(
        f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
    ) == {
        "value": Decimal(22001),
        "version": 15,
    }

    # Restore delete row
    api_client.patch(
        reverse(
            "api:trash:restore",
        ),
        {
            "trash_item_type": "row",
            "trash_item_id": row3["id"],
            "parent_trash_item_id": table.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert (
        cache.get(
            f"aggregation_version__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
        )
        == 17
    )

    check_table_2_aggregation_values(
        {sum_formula_on_lookup_field.db_column: 22201}, "after row restoration"
    )

    # Should store the new value/version in cache
    assert cache.get(
        f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
    ) == {
        "value": Decimal(22201),
        "version": 17,
    }

    # Update number field
    api_client.patch(
        reverse(
            "api:database:fields:item",
            kwargs={"field_id": number_field.id},
        ),
        {"number_decimal_places": 1},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    # Cache version should be incremented
    assert (
        cache.get(
            f"aggregation_version__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
        )
        == 18
    )

    check_table_2_aggregation_values(
        {sum_formula_on_lookup_field.db_column: 22201}, "after field modification"
    )

    assert cache.get(
        f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
    ) == {
        "value": Decimal(22201),
        "version": 18,
    }

    # Delete number field
    api_client.delete(
        reverse(
            "api:database:fields:item",
            kwargs={"field_id": number_field.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert cache.get(
        f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
    ) == {
        "value": Decimal(22201),
        "version": 18,
    }
    assert (
        cache.get(
            f"aggregation_version__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
        )
        == 19
    )

    check_table_2_aggregation_values({}, "after field deletion")

    # No modification as the field and the aggregation don't exist
    assert cache.get(
        f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
    ) == {
        "value": Decimal(22201),
        "version": 18,
    }
    assert (
        cache.get(
            f"aggregation_version__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
        )
        == 19
    )

    # Restore deleted field
    resp = api_client.patch(
        reverse(
            "api:trash:restore",
        ),
        {
            "trash_item_type": "field",
            "trash_item_id": number_field.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response = api_client.get(
        url,
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.json() == {number_field.db_column: 11101}

    # The field aggregation has been automatically deleted so no aggregations anymore
    check_table_2_aggregation_values({}, "after field restoration")

    # Still no modifications
    assert cache.get(
        f"aggregation_value__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
    ) == {
        "value": Decimal(22201),
        "version": 18,
    }
    assert (
        cache.get(
            f"aggregation_version__{grid2.id}_{sum_formula_on_lookup_field.db_column}"
        )
        == 19
    )


@pytest.mark.django_db
def test_can_get_aggregation_if_result_is_nan(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    # This formula will resolve  as NaN for every row
    formula_field = data_fixture.create_formula_field(table=table, formula="1 / 0")

    model = table.get_model()
    model.objects.create()

    ViewHandler().update_field_options(
        view=grid_view,
        field_options={
            formula_field.id: {
                "aggregation_type": "sum",
                "aggregation_raw_type": "sum",
            }
        },
    )

    url = reverse(
        "api:database:views:grid:field-aggregations",
        kwargs={"view_id": grid_view.id},
    )

    response = api_client.get(
        url,
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_200_OK
    assert response.json() == {f"field_{formula_field.id}": "NaN"}


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
    assert response_json["field_options"][str(text_field.id)]["aggregation_type"] == ""
    assert (
        response_json["field_options"][str(text_field.id)]["aggregation_raw_type"] == ""
    )
    assert response_json["field_options"][str(number_field.id)]["width"] == 200
    assert response_json["field_options"][str(number_field.id)]["hidden"] is False
    assert response_json["field_options"][str(number_field.id)]["order"] == 32767
    assert (
        response_json["field_options"][str(number_field.id)]["aggregation_type"] == ""
    )
    assert (
        response_json["field_options"][str(number_field.id)]["aggregation_raw_type"]
        == ""
    )
    options = grid.get_field_options()
    assert len(options) == 2
    assert options[0].field_id == text_field.id
    assert options[0].width == 300
    assert options[0].hidden is True
    assert options[0].order == 32767
    assert options[0].aggregation_type == ""
    assert options[0].aggregation_raw_type == ""
    assert options[1].field_id == number_field.id
    assert options[1].width == 200
    assert options[1].hidden is False
    assert options[1].order == 32767
    assert options[1].aggregation_type == ""
    assert options[1].aggregation_raw_type == ""

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
        {"field_options": {text_field.id: {"width": "abc"}}},
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
        {"field_options": {text_field.id: {"hidden": "abc"}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["field_options"][0]["code"] == "invalid_value"

    # Test unregistered aggregation type
    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url,
        {"field_options": {text_field.id: {"aggregation_raw_type": "foo"}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["field_options"][0]["code"] == "invalid_value"

    # Test aggregation type that doesn't support the field
    # Fake incompatible field
    empty_count = view_aggregation_type_registry.get("empty_count")
    empty_count.field_is_compatible = lambda _: False

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url,
        {"field_options": {text_field.id: {"aggregation_raw_type": "empty_count"}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_AGGREGATION_DOES_NOT_SUPPORTED_FIELD"
    assert (
        response_json["detail"]
        == "The aggregation type does not support the given field."
    )

    empty_count.field_is_compatible = lambda _: True


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
    assert "decorations" not in response_json

    response = api_client.post(
        "{}?include=filters,sortings,decorations".format(
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
    assert response_json["decorations"] == []

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
    assert "decorations" not in response_json


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
    assert "decorations" not in response_json

    view.refresh_from_db()
    assert view.filter_type == "OR"
    assert view.filters_disabled

    filter_1 = data_fixture.create_view_filter(view=view)
    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.patch(
        "{}?include=filters,sortings,decorations".format(url),
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
    assert response_json["decorations"] == []


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
        reverse("api:database:views:public_info", kwargs={"slug": grid_view.slug})
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
                "read_only": False,
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
            "row_identifier_type": grid_view.row_identifier_type,
            "show_logo": True,
        },
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
                "aggregation_type": "",
                "aggregation_raw_type": "",
            },
        },
    }


@pytest.mark.django_db
def test_list_rows_public_with_query_param_filter(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    public_field = data_fixture.create_text_field(table=table, name="public")
    hidden_field = data_fixture.create_text_field(table=table, name="hidden")
    grid_view = data_fixture.create_grid_view(
        table=table, user=user, public=True, create_options=False
    )
    data_fixture.create_grid_view_field_option(grid_view, public_field, hidden=False)
    data_fixture.create_grid_view_field_option(grid_view, hidden_field, hidden=True)

    first_row = RowHandler().create_row(
        user, table, values={"public": "a", "hidden": "y"}, user_field_names=True
    )
    RowHandler().create_row(
        user, table, values={"public": "b", "hidden": "z"}, user_field_names=True
    )

    url = reverse(
        "api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug}
    )
    get_params = [f"filter__field_{public_field.id}__contains=a"]
    response = api_client.get(f'{url}?{"&".join(get_params)}')
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == first_row.id

    url = reverse(
        "api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug}
    )
    get_params = [
        f"filter__field_{public_field.id}__contains=a",
        f"filter__field_{public_field.id}__contains=b",
        f"filter_type=OR",
    ]
    response = api_client.get(f'{url}?{"&".join(get_params)}')
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["results"]) == 2

    url = reverse(
        "api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug}
    )
    get_params = [f"filter__field_{hidden_field.id}__contains=y"]
    response = api_client.get(f'{url}?{"&".join(get_params)}')
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_FILTER_FIELD_NOT_FOUND"

    url = reverse(
        "api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug}
    )
    get_params = [f"filter__field_{public_field.id}__random=y"]
    response = api_client.get(f'{url}?{"&".join(get_params)}')
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST"

    url = reverse(
        "api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug}
    )
    get_params = [f"filter__field_{public_field.id}__higher_than=1"]
    response = api_client.get(f'{url}?{"&".join(get_params)}')
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD"


@pytest.mark.django_db
def test_list_rows_public_with_query_param_order(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(database=table.database)
    public_field = data_fixture.create_text_field(table=table, name="public")
    hidden_field = data_fixture.create_text_field(table=table, name="hidden")
    link_row_field = FieldHandler().create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Link",
        link_row_table=table_2,
    )
    grid_view = data_fixture.create_grid_view(
        table=table, user=user, public=True, create_options=False
    )
    data_fixture.create_grid_view_field_option(grid_view, public_field, hidden=False)
    data_fixture.create_grid_view_field_option(grid_view, hidden_field, hidden=True)
    data_fixture.create_grid_view_field_option(grid_view, link_row_field, hidden=False)

    first_row = RowHandler().create_row(
        user, table, values={"public": "a", "hidden": "y"}, user_field_names=True
    )
    second_row = RowHandler().create_row(
        user, table, values={"public": "b", "hidden": "z"}, user_field_names=True
    )

    url = reverse(
        "api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug}
    )
    response = api_client.get(
        f"{url}?order_by=-field_{public_field.id}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["results"]) == 2
    assert response_json["results"][0]["id"] == second_row.id
    assert response_json["results"][1]["id"] == first_row.id

    url = reverse(
        "api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug}
    )
    response = api_client.get(
        f"{url}?order_by=field_{hidden_field.id}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_ORDER_BY_FIELD_NOT_FOUND"

    url = reverse(
        "api:database:views:grid:public_rows", kwargs={"slug": grid_view.slug}
    )
    response = api_client.get(
        f"{url}?order_by=field_{link_row_field.id}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_ORDER_BY_FIELD_NOT_POSSIBLE"


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


@pytest.mark.django_db
def test_grid_view_link_row_lookup_view(api_client, data_fixture):
    field_handler = FieldHandler()
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)
    lookup_table = data_fixture.create_database_table(database=database)
    grid = data_fixture.create_grid_view(table=table)
    grid_2 = data_fixture.create_grid_view()
    text_field = data_fixture.create_text_field(table=table)
    link_row_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        link_row_table=lookup_table,
        name="Link row 1",
    )
    disabled_link_row_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        link_row_table=lookup_table,
        name="Link row 2",
    )
    unrelated_link_row_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        link_row_table=lookup_table,
        name="Link row 3",
    )
    primary_related_field = data_fixture.create_text_field(
        table=lookup_table, primary=True
    )
    data_fixture.create_text_field(table=lookup_table)
    data_fixture.create_grid_view_field_option(grid, text_field, hidden=False, order=1)
    data_fixture.create_grid_view_field_option(
        grid, link_row_field, hidden=False, order=2
    )
    data_fixture.create_grid_view_field_option(
        grid, disabled_link_row_field, hidden=True, order=3
    )
    data_fixture.create_grid_view_field_option(
        grid, unrelated_link_row_field, hidden=True, order=4
    )
    data_fixture.create_grid_view_field_option(
        grid_2, unrelated_link_row_field, hidden=False, order=1
    )

    lookup_model = lookup_table.get_model()
    i1 = lookup_model.objects.create(**{f"field_{primary_related_field.id}": "Test 1"})
    i2 = lookup_model.objects.create(**{f"field_{primary_related_field.id}": "Test 2"})
    i3 = lookup_model.objects.create(**{f"field_{primary_related_field.id}": "Test 3"})
    i4 = lookup_model.objects.create(**{f"field_{primary_related_field.id}": "Test 4"})

    # Because the `restrict_link_row_public_view_sharing` property is True for the
    # grid view type, only related values that have relationship with the table and
    # are visible in the view will be exposed via the endpoint. By adding the first
    # three to the row that matches the filters, the fourth one, should never be
    # visible via this endpoint.
    model = table.get_model()
    row = model.objects.create(**{f"field_{text_field.id}": "match"})
    getattr(row, f"field_{link_row_field.id}").add(i1.id, i2.id, i3.id)
    row_2 = model.objects.create(**{f"field_{text_field.id}": "no match"})
    getattr(row_2, f"field_{link_row_field.id}").add(i4.id)

    # Anonymous, not existing slug.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": "NOT_EXISTING", "field_id": link_row_field.id},
    )
    response = api_client.get(url, {})
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    # Anonymous, existing slug, but form is not public.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": grid.slug, "field_id": link_row_field.id},
    )
    response = api_client.get(url, format="json")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    # user that doesn't have access to the group, existing slug, but form is not public.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": grid.slug, "field_id": link_row_field.id},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token_2}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    # valid user, existing slug, but invalid wrong field type.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": grid.slug, "field_id": text_field.id},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FIELD_DOES_NOT_EXIST"

    # valid user, existing slug, but invalid wrong field type.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": grid.slug, "field_id": 0},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FIELD_DOES_NOT_EXIST"

    # valid user, existing slug, but disabled link row field.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": grid.slug, "field_id": disabled_link_row_field.id},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FIELD_DOES_NOT_EXIST"

    # valid user, existing slug, but unrelated link row field.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": grid.slug, "field_id": unrelated_link_row_field.id},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FIELD_DOES_NOT_EXIST"

    grid.public = True
    grid.save()

    # anonymous, existing slug, public form, correct link row field without any
    # filters applied to the view.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": grid.slug, "field_id": link_row_field.id},
    )
    response = api_client.get(
        url,
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 4
    assert len(response_json["results"]) == 4

    # anonymous, existing slug, public form, correct link row field after applying a
    # filter.
    data_fixture.create_view_filter(user, view=grid, field=text_field, value="match")
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": grid.slug, "field_id": link_row_field.id},
    )
    response = api_client.get(
        url,
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 3
    assert len(response_json["results"]) == 3
    assert response_json["results"][0]["id"] == i1.id
    assert response_json["results"][0]["value"] == "Test 1"
    assert len(response_json["results"][0]) == 2
    assert response_json["results"][1]["id"] == i2.id
    assert response_json["results"][2]["id"] == i3.id

    # same as before only now with search.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": grid.slug, "field_id": link_row_field.id},
    )
    response = api_client.get(
        f"{url}?search=Test 2",
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == i2.id
    assert response_json["results"][0]["value"] == "Test 2"

    # same as before only now with pagination
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": grid.slug, "field_id": link_row_field.id},
    )
    response = api_client.get(
        f"{url}?size=1&page=2",
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 3
    assert response_json["next"] is not None
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == i2.id
    assert response_json["results"][0]["value"] == "Test 2"


@pytest.mark.django_db
def test_list_rows_include_fields(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(database=table.database)
    text_field = data_fixture.create_text_field(
        table=table, order=0, name="Color", text_default="white"
    )
    number_field = data_fixture.create_number_field(
        table=table, order=1, name="Horsepower"
    )
    boolean_field = data_fixture.create_boolean_field(
        table=table, order=2, name="For sale"
    )
    link_row_field = FieldHandler().create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Link",
        link_row_table=table_2,
    )
    primary_field = data_fixture.create_text_field(table=table_2, primary=True)
    lookup_model = table_2.get_model()
    i1 = lookup_model.objects.create(**{f"field_{primary_field.id}": "Test 1"})
    i2 = lookup_model.objects.create(**{f"field_{primary_field.id}": "Test 2"})
    i3 = lookup_model.objects.create(**{f"field_{primary_field.id}": "Test 3"})

    grid = data_fixture.create_grid_view(table=table)
    data_fixture.create_grid_view_field_option(grid, link_row_field, hidden=False)

    model = grid.table.get_model()
    row_1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Green",
            f"field_{number_field.id}": 10,
            f"field_{boolean_field.id}": False,
        }
    )
    getattr(row_1, f"field_{link_row_field.id}").add(i1.id)
    row_2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Orange",
            f"field_{number_field.id}": 100,
            f"field_{boolean_field.id}": True,
        }
    )
    getattr(row_2, f"field_{link_row_field.id}").add(i2.id)
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": "Purple",
            f"field_{number_field.id}": 1000,
            f"field_{boolean_field.id}": False,
        }
    )
    getattr(row_3, f"field_{link_row_field.id}").add(i3.id)

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(
        url,
        {
            "include_fields": f"\
                field_{text_field.id},\
                field_{number_field.id},\
                field_{link_row_field.id}",
            "exclude_fields": f"field_{number_field.id}",
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    # Confirm that text_field is included
    assert response_json["results"][0][f"field_{text_field.id}"] == "Green"
    assert response_json["results"][1][f"field_{text_field.id}"] == "Orange"
    assert response_json["results"][2][f"field_{text_field.id}"] == "Purple"

    # Confirm that number_field is excluded
    assert f"field_{number_field.id}" not in response_json["results"][0]
    assert f"field_{number_field.id}" not in response_json["results"][1]
    assert f"field_{number_field.id}" not in response_json["results"][2]

    # Confirm that boolean_field is not returned
    assert f"field_{boolean_field.id}" not in response_json["results"][0]
    assert f"field_{boolean_field.id}" not in response_json["results"][1]
    assert f"field_{boolean_field.id}" not in response_json["results"][2]

    # Confirm that link_row_field is included
    assert (
        response_json["results"][0][f"field_{link_row_field.id}"][0]["value"]
        == "Test 1"
    )
    assert (
        response_json["results"][1][f"field_{link_row_field.id}"][0]["value"]
        == "Test 2"
    )
    assert (
        response_json["results"][2][f"field_{link_row_field.id}"][0]["value"]
        == "Test 3"
    )

    # Confirm that id and order are still returned
    assert "id" in response_json["results"][0]
    assert "id" in response_json["results"][1]
    assert "id" in response_json["results"][2]
    assert "order" in response_json["results"][0]
    assert "order" in response_json["results"][1]
    assert "order" in response_json["results"][2]

    # include_fields is empty
    response = api_client.get(
        url,
        {"include_fields": ""},
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    # Should return response with no fields
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert "id" in response_json["results"][0]
    assert "order" in response_json["results"][0]
    assert f"field_{text_field.id}" not in response_json["results"][0]
    assert f"field_{number_field.id}" not in response_json["results"][0]
    assert f"field_{boolean_field.id}" not in response_json["results"][0]

    # Test invalid fields
    response = api_client.get(
        url,
        {"include_fields": "field_9999"},
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    # Should also return response with no fields
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert "id" in response_json["results"][0]
    assert "id" in response_json["results"][0]
    assert "order" in response_json["results"][0]
    assert f"field_{text_field.id}" not in response_json["results"][0]
    assert f"field_{number_field.id}" not in response_json["results"][0]
    assert f"field_{boolean_field.id}" not in response_json["results"][0]


@pytest.mark.django_db
def test_user_with_wrong_password_cant_get_info_about_a_public_password_protected_grid_view(
    api_client, data_fixture
):
    user = data_fixture.create_user()
    grid_view = data_fixture.create_public_password_protected_grid_view(
        user=user, password="12345678"
    )

    response = api_client.post(
        reverse("api:database:views:public_auth", kwargs={"slug": grid_view.slug}),
        {"password": "wrong_password"},
        format="json",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED

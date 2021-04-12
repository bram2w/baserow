import pytest

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from django.shortcuts import reverse


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

    filter = data_fixture.create_view_filter(view=grid, field=text_field, value="Green")
    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_1.id
    filter.delete()

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
def test_patch_grid_view(api_client, data_fixture):
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
    grid_2 = data_fixture.create_grid_view()

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
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

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
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

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
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

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url, {}, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
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

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url,
        {"field_options": {99999: {"width": 100}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_UNRELATED_FIELD"

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url,
        {"field_options": {99999: {"hidden": True}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_UNRELATED_FIELD"

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
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

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
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

    url = reverse("api:database:views:grid:list", kwargs={"view_id": 999})
    response = api_client.patch(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GRID_DOES_NOT_EXIST"

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid_2.id})
    response = api_client.patch(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

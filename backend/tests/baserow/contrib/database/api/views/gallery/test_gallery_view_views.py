import pytest
from django.shortcuts import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)


@pytest.mark.django_db
def test_list_rows(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(
        table=table, order=0, name="Color", text_default="white"
    )
    gallery = data_fixture.create_gallery_view(table=table)
    gallery_2 = data_fixture.create_gallery_view()

    model = gallery.table.get_model()
    row_1 = model.objects.create(**{f"field_{text_field.id}": "Green"})
    row_2 = model.objects.create()
    row_3 = model.objects.create(**{f"field_{text_field.id}": "Orange"})
    row_4 = model.objects.create(**{f"field_{text_field.id}": "Purple"})

    url = reverse("api:database:views:gallery:list", kwargs={"view_id": 999})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GALLERY_DOES_NOT_EXIST"

    url = reverse("api:database:views:gallery:list", kwargs={"view_id": gallery_2.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:views:gallery:list", kwargs={"view_id": gallery.id})
    response = api_client.get(
        url, {"limit": 2}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert response_json["results"][0]["id"] == row_1.id
    assert response_json["results"][1]["id"] == row_2.id
    assert "field_options" not in response_json

    url = reverse("api:database:views:gallery:list", kwargs={"view_id": gallery.id})
    response = api_client.get(
        url, {"limit": 1, "offset": 2}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert response_json["results"][0]["id"] == row_3.id

    sort = data_fixture.create_view_sort(view=gallery, field=text_field, order="ASC")
    url = reverse("api:database:views:gallery:list", kwargs={"view_id": gallery.id})
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
        view=gallery, field=text_field, value="Green"
    )
    url = reverse("api:database:views:gallery:list", kwargs={"view_id": gallery.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_1.id
    view_filter.delete()

    url = reverse("api:database:views:gallery:list", kwargs={"view_id": gallery.id})
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

    url = reverse("api:database:views:gallery:list", kwargs={"view_id": gallery.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 0
    assert not response_json["previous"]
    assert not response_json["next"]
    assert len(response_json["results"]) == 0

    url = reverse("api:database:views:gallery:list", kwargs={"view_id": gallery.id})
    response = api_client.get(url)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    data_fixture.create_template(group=gallery.table.database.group)
    url = reverse("api:database:views:gallery:list", kwargs={"view_id": gallery.id})
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
    gallery = data_fixture.create_gallery_view(table=table)

    # The second field is deliberately created after the creation of the gallery field
    # so that the GridViewFieldOptions entry is not created. This should
    # automatically be created when the page is fetched.
    number_field = data_fixture.create_number_field(
        table=table, order=1, name="Horsepower"
    )

    url = reverse("api:database:views:gallery:list", kwargs={"view_id": gallery.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert "field_options" not in response_json

    url = reverse("api:database:views:gallery:list", kwargs={"view_id": gallery.id})
    response = api_client.get(
        url, {"include": "field_options"}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["field_options"]) == 2
    assert response_json["field_options"][str(text_field.id)]["hidden"] is True
    assert response_json["field_options"][str(text_field.id)]["order"] == 32767
    assert response_json["field_options"][str(number_field.id)]["hidden"] is True
    assert response_json["field_options"][str(number_field.id)]["order"] == 32767
    assert "filters_disabled" not in response_json


@pytest.mark.django_db
def test_patch_gallery_view_field_options(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
    )
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    gallery = data_fixture.create_gallery_view(table=table)

    url = reverse("api:database:views:field_options", kwargs={"view_id": gallery.id})
    response = api_client.patch(
        url,
        {"field_options": {text_field.id: {"width": 300, "hidden": False}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["field_options"]) == 1
    assert response_json["field_options"][str(text_field.id)]["hidden"] is False
    assert response_json["field_options"][str(text_field.id)]["order"] == 32767
    options = gallery.get_field_options()
    assert len(options) == 1
    assert options[0].field_id == text_field.id
    assert options[0].hidden is False
    assert options[0].order == 32767


@pytest.mark.django_db
def test_create_gallery_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "name": "Test 2",
            "type": "gallery",
            "filter_type": "AND",
            "filters_disabled": False,
            "card_cover_image_field": file_field.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Test 2"
    assert response_json["type"] == "gallery"
    assert response_json["filter_type"] == "AND"
    assert response_json["filters_disabled"] is False
    assert response_json["card_cover_image_field"] == file_field.id


@pytest.mark.django_db
def test_create_gallery_view_invalid_card_card_cover_image_field(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    text = data_fixture.create_text_field(table=table)
    file_field = data_fixture.create_file_field()

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {"name": "Test 2", "type": "gallery", "card_cover_image_field": text.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response_json["detail"]["card_cover_image_field"][0]["code"] == "does_not_exist"
    )

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {"name": "Test 2", "type": "gallery", "card_cover_image_field": file_field.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_FIELD_NOT_IN_TABLE"


@pytest.mark.django_db
def test_update_gallery_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    gallery_view = data_fixture.create_gallery_view(table=table)

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": gallery_view.id}),
        {
            "name": "Test 2",
            "type": "gallery",
            "filter_type": "AND",
            "filters_disabled": False,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Test 2"
    assert response_json["type"] == "gallery"
    assert response_json["filter_type"] == "AND"
    assert response_json["filters_disabled"] is False

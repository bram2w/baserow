import pytest

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from django.shortcuts import reverse

from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import ViewFilter
from baserow.contrib.database.views.registries import (
    view_type_registry,
    view_filter_type_registry,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
def test_list_view_filters(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    field_1 = data_fixture.create_text_field(table=table_1)
    field_2 = data_fixture.create_text_field(table=table_1)
    field_3 = data_fixture.create_text_field(table=table_2)
    view_1 = data_fixture.create_grid_view(table=table_1, order=1)
    view_2 = data_fixture.create_grid_view(table=table_1, order=2)
    view_3 = data_fixture.create_grid_view(table=table_2, order=1)
    filter_1 = data_fixture.create_view_filter(view=view_1, field=field_1)
    filter_2 = data_fixture.create_view_filter(view=view_1, field=field_2)
    data_fixture.create_view_filter(view=view_2, field=field_1)
    data_fixture.create_view_filter(view=view_3, field=field_3)

    response = api_client.get(
        reverse("api:database:views:list_filters", kwargs={"view_id": view_3.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        reverse("api:database:views:list_filters", kwargs={"view_id": 999999}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    response = api_client.get(
        reverse("api:database:views:list_filters", kwargs={"view_id": view_1.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert len(response_json) == 2
    assert response_json[0]["id"] == filter_1.id
    assert response_json[0]["view"] == view_1.id
    assert response_json[0]["field"] == field_1.id
    assert response_json[0]["type"] == filter_1.type
    assert response_json[0]["value"] == filter_1.value
    assert response_json[0]["preload_values"] == {}
    assert response_json[1]["id"] == filter_2.id

    response = api_client.delete(
        reverse("api:groups:item", kwargs={"group_id": table_1.database.group.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT
    response = api_client.get(
        reverse("api:database:views:list_filters", kwargs={"view_id": view_1.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_create_view_filter(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    field_1 = data_fixture.create_text_field(table=table_1)
    field_2 = data_fixture.create_text_field(table=table_2)
    view_1 = data_fixture.create_grid_view(table=table_1)
    view_2 = data_fixture.create_grid_view(table=table_2)

    response = api_client.post(
        reverse("api:database:views:list_filters", kwargs={"view_id": view_2.id}),
        {"field": field_2.id, "type": "equal", "value": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.post(
        reverse("api:database:views:list_filters", kwargs={"view_id": 99999}),
        {"field": field_1.id, "type": "equal", "value": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    response = api_client.post(
        reverse("api:database:views:list_filters", kwargs={"view_id": view_1.id}),
        {"field": 9999999, "type": "NOT_EXISTING", "not_value": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["field"][0]["code"] == "does_not_exist"
    assert response_json["detail"]["type"][0]["code"] == "invalid_choice"

    response = api_client.post(
        reverse("api:database:views:list_filters", kwargs={"view_id": view_1.id}),
        {"field": field_2.id, "type": "equal", "value": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_FIELD_NOT_IN_TABLE"

    grid_view_type = view_type_registry.get("grid")
    grid_view_type.can_filter = False
    response = api_client.post(
        reverse("api:database:views:list_filters", kwargs={"view_id": view_1.id}),
        {"field": field_1.id, "type": "equal", "value": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_VIEW_FILTER_NOT_SUPPORTED"
    grid_view_type.can_filter = True

    equal_filter_type = view_filter_type_registry.get("equal")
    allowed = equal_filter_type.compatible_field_types
    equal_filter_type.compatible_field_types = []
    response = api_client.post(
        reverse("api:database:views:list_filters", kwargs={"view_id": view_1.id}),
        {"field": field_1.id, "type": "equal", "value": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD"
    equal_filter_type.compatible_field_types = allowed

    response = api_client.post(
        reverse("api:database:views:list_filters", kwargs={"view_id": view_1.id}),
        {"field": field_1.id, "type": "equal", "value": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert ViewFilter.objects.all().count() == 1
    first = ViewFilter.objects.all().first()
    assert response_json["id"] == first.id
    assert response_json["view"] == view_1.id
    assert response_json["field"] == field_1.id
    assert response_json["type"] == "equal"
    assert response_json["value"] == "test"

    response = api_client.post(
        reverse("api:database:views:list_filters", kwargs={"view_id": view_1.id}),
        {"field": field_1.id, "type": "equal", "value": ""},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["value"] == ""

    response = api_client.post(
        reverse("api:database:views:list_filters", kwargs={"view_id": view_1.id}),
        {"field": field_1.id, "type": "equal"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["value"] == ""


@pytest.mark.django_db
def test_get_view_filter(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    filter_1 = data_fixture.create_view_filter(user=user, value="test")
    filter_2 = data_fixture.create_view_filter()

    response = api_client.get(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_2.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        reverse("api:database:views:filter_item", kwargs={"view_filter_id": 99999}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_FILTER_DOES_NOT_EXIST"

    response = api_client.get(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_1.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert ViewFilter.objects.all().count() == 2
    first = ViewFilter.objects.get(pk=filter_1.id)
    assert response_json["id"] == first.id
    assert response_json["view"] == first.view_id
    assert response_json["field"] == first.field_id
    assert response_json["type"] == "equal"
    assert response_json["value"] == "test"

    response = api_client.delete(
        reverse(
            "api:groups:item",
            kwargs={"group_id": filter_1.view.table.database.group.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT

    response = api_client.get(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_1.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_FILTER_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_get_link_row_filter_type_preload_values(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)
    related_table = data_fixture.create_database_table(database=database)
    related_primary_field = data_fixture.create_text_field(
        table=related_table, primary=True
    )
    grid_view = data_fixture.create_grid_view(table=table)

    field_handler = FieldHandler()
    link_row_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Test",
        link_row_table=related_table,
    )
    row_handler = RowHandler()
    related_model = related_table.get_model()

    related_row_1 = row_handler.create_row(
        user=user,
        table=related_table,
        model=related_model,
        values={
            f"field_{related_primary_field.id}": "Related row 1",
        },
    )
    view_filter = data_fixture.create_view_filter(
        view=grid_view,
        field=link_row_field,
        type="link_row_has",
        value=f"{related_row_1.id}",
    )
    response = api_client.get(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": view_filter.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["preload_values"] == {"display_name": "Related row 1"}


@pytest.mark.django_db
def test_update_view_filter(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    filter_1 = data_fixture.create_view_filter(user=user, value="test")
    filter_2 = data_fixture.create_view_filter()
    field_1 = data_fixture.create_text_field(table=filter_1.view.table)
    field_2 = data_fixture.create_text_field()

    response = api_client.patch(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_2.id}
        ),
        {"value": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.patch(
        reverse("api:database:views:filter_item", kwargs={"view_filter_id": 9999}),
        {"value": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_FILTER_DOES_NOT_EXIST"

    response = api_client.patch(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_1.id}
        ),
        {
            "field": 9999999,
            "type": "NOT_EXISTING",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["field"][0]["code"] == "does_not_exist"
    assert response_json["detail"]["type"][0]["code"] == "invalid_choice"

    response = api_client.patch(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_1.id}
        ),
        {"field": field_2.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_FIELD_NOT_IN_TABLE"

    equal_filter_type = view_filter_type_registry.get("not_equal")
    allowed = equal_filter_type.compatible_field_types
    equal_filter_type.compatible_field_types = []
    grid_view_type = view_type_registry.get("grid")
    grid_view_type.can_filter = False
    response = api_client.patch(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_1.id}
        ),
        {"type": "not_equal"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    grid_view_type.can_filter = True
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD"
    equal_filter_type.compatible_field_types = allowed

    response = api_client.patch(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_1.id}
        ),
        {"field": field_1.id, "type": "not_equal", "value": "test 2"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert ViewFilter.objects.all().count() == 2
    first = ViewFilter.objects.get(pk=filter_1.id)
    assert first.field_id == field_1.id
    assert first.type == "not_equal"
    assert first.value == "test 2"
    assert response_json["id"] == first.id
    assert response_json["view"] == first.view_id
    assert response_json["field"] == field_1.id
    assert response_json["type"] == "not_equal"
    assert response_json["value"] == "test 2"

    response = api_client.patch(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_1.id}
        ),
        {"type": "equal"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    first = ViewFilter.objects.get(pk=filter_1.id)
    assert first.field_id == field_1.id
    assert first.type == "equal"
    assert first.value == "test 2"
    assert response_json["id"] == first.id
    assert response_json["field"] == field_1.id
    assert response_json["type"] == "equal"
    assert response_json["value"] == "test 2"

    response = api_client.patch(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_1.id}
        ),
        {"value": "test 3"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    first = ViewFilter.objects.get(pk=filter_1.id)
    assert first.field_id == field_1.id
    assert first.type == "equal"
    assert first.value == "test 3"
    assert response_json["id"] == first.id
    assert response_json["view"] == first.view_id
    assert response_json["field"] == field_1.id
    assert response_json["type"] == "equal"
    assert response_json["value"] == "test 3"

    response = api_client.patch(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_1.id}
        ),
        {"value": ""},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    first = ViewFilter.objects.get(pk=filter_1.id)
    assert first.value == ""
    assert response_json["value"] == ""


@pytest.mark.django_db
def test_delete_view_filter(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    filter_1 = data_fixture.create_view_filter(user=user, value="test")
    filter_2 = data_fixture.create_view_filter()

    response = api_client.delete(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_2.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.delete(
        reverse("api:database:views:filter_item", kwargs={"view_filter_id": 9999}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_FILTER_DOES_NOT_EXIST"

    response = api_client.delete(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": filter_1.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 204
    assert ViewFilter.objects.all().count() == 1


@pytest.mark.django_db
def test_list_views_including_filters(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    field_1 = data_fixture.create_text_field(table=table_1)
    field_2 = data_fixture.create_text_field(table=table_1)
    field_3 = data_fixture.create_text_field(table=table_2)
    view_1 = data_fixture.create_grid_view(table=table_1, order=1)
    view_2 = data_fixture.create_grid_view(table=table_1, order=2)
    view_3 = data_fixture.create_grid_view(table=table_2, order=1)
    filter_1 = data_fixture.create_view_filter(view=view_1, field=field_1)
    filter_2 = data_fixture.create_view_filter(view=view_1, field=field_2)
    filter_3 = data_fixture.create_view_filter(view=view_2, field=field_1)
    data_fixture.create_view_filter(view=view_3, field=field_3)

    response = api_client.get(
        "{}".format(
            reverse("api:database:views:list", kwargs={"table_id": table_1.id})
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 2
    assert "filters" not in response_json[0]
    assert "filters" not in response_json[1]

    response = api_client.get(
        "{}?include=filters".format(
            reverse("api:database:views:list", kwargs={"table_id": table_1.id})
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert len(response_json[0]["filters"]) == 2
    assert response_json[0]["filters"][0]["id"] == filter_1.id
    assert response_json[0]["filters"][0]["view"] == view_1.id
    assert response_json[0]["filters"][0]["field"] == field_1.id
    assert response_json[0]["filters"][0]["type"] == filter_1.type
    assert response_json[0]["filters"][0]["value"] == filter_1.value
    assert response_json[0]["filters"][1]["id"] == filter_2.id
    assert len(response_json[1]["filters"]) == 1
    assert response_json[1]["filters"][0]["id"] == filter_3.id


@pytest.mark.django_db
def test_cant_update_view_filter_when_view_trashed(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    grid_view = data_fixture.create_grid_view(user=user)
    view_filter = data_fixture.create_view_filter(user=user, view=grid_view)

    ViewHandler().delete_view(user, grid_view)

    response = api_client.patch(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": view_filter.id}
        ),
        data={"value": "new value"},
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_cant_delete_view_filter_when_view_trashed(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    grid_view = data_fixture.create_grid_view(user=user)
    view_filter = data_fixture.create_view_filter(user=user, view=grid_view)

    ViewHandler().delete_view(user, grid_view)

    response = api_client.delete(
        reverse(
            "api:database:views:filter_item", kwargs={"view_filter_id": view_filter.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND

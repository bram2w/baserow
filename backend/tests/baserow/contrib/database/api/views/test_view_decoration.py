from django.shortcuts import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from baserow.contrib.database.views.models import ViewDecoration
from baserow.contrib.database.views.registries import view_type_registry


@pytest.mark.django_db
def test_list_view_decorations(api_client, data_fixture):
    data_fixture.register_temp_decorators_and_value_providers()
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    view_1 = data_fixture.create_grid_view(table=table_1, order=1)
    view_2 = data_fixture.create_grid_view(table=table_1, order=2)
    view_3 = data_fixture.create_grid_view(table=table_2, order=1)
    decoration_1 = data_fixture.create_view_decoration(view=view_1, order=1)
    decoration_2 = data_fixture.create_view_decoration(
        view=view_1,
        type="tmp_decorator_type_2",
        value_provider_type="conditional_color",
        order=2,
    )
    data_fixture.create_view_decoration(view=view_2, order=3)
    data_fixture.create_view_decoration(view=view_3, order=4)

    response = api_client.get(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_3.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        reverse("api:database:views:list_decorations", kwargs={"view_id": 999999}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    response = api_client.get(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_1.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()

    assert len(response_json) == 2
    assert response_json[0]["id"] == decoration_1.id
    assert response_json[0]["view"] == view_1.id
    assert response_json[0]["type"] == decoration_1.type
    assert response_json[0]["value_provider_type"] == decoration_1.value_provider_type
    assert response_json[1]["id"] == decoration_2.id
    assert response_json[1]["type"] == decoration_2.type
    assert response_json[1]["value_provider_type"] == decoration_2.value_provider_type

    response = api_client.delete(
        reverse(
            "api:workspaces:item",
            kwargs={"workspace_id": table_1.database.workspace.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT
    response = api_client.get(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_1.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_create_view_decoration(api_client, data_fixture):
    data_fixture.register_temp_decorators_and_value_providers()
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    view_1 = data_fixture.create_grid_view(table=table_1)
    view_2 = data_fixture.create_grid_view(table=table_2)

    response = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_2.id}),
        {
            "type": "tmp_decorator_type_1",
            "value_provider_type": "",
            "value_provider_conf": {},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": 99999}),
        {
            "type": "tmp_decorator_type_1",
            "value_provider_type": "",
            "value_provider_conf": {},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    grid_view_type = view_type_registry.get("grid")
    grid_view_type.can_decorate = False
    response = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_1.id}),
        {
            "type": "tmp_decorator_type_1",
            "value_provider_type": "",
            "value_provider_conf": {},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_VIEW_DECORATION_NOT_SUPPORTED"
    grid_view_type.can_decorate = True

    response = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_1.id}),
        {
            "type": "bad_type",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"] == {
        "type": [
            {"error": '"bad_type" is not a valid choice.', "code": "invalid_choice"}
        ]
    }

    response = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_1.id}),
        {
            "type": "tmp_decorator_type_1",
            "value_provider_type": "bad_type",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"] == {
        "value_provider_type": [
            {"error": '"bad_type" is not a valid choice.', "code": "invalid_choice"}
        ]
    }

    response = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_1.id}),
        {
            "type": "tmp_decorator_type_1",
            "value_provider_type": "",
            "value_provider_conf": {"foo": "barr"},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"] == {
        "value_provider_conf": [
            {"error": "This field should be an empty object.", "code": "invalid"}
        ]
    }

    response = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_1.id}),
        {
            "type": "tmp_decorator_type_1",
            "value_provider_type": "value_provider_1",
            "value_provider_conf": {"colors": "error"},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"] == {
        "value_provider_conf": {
            "field_id": [{"error": "This field is required.", "code": "required"}]
        }
    }

    response = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_1.id}),
        {
            "type": "tmp_decorator_type_1",
            "value_provider_type": "value_provider_3",
            "value_provider_conf": {"field_id": 1},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert (
        response_json["error"] == "ERROR_VIEW_DECORATION_VALUE_PROVIDER_NOT_COMPATIBLE"
    )

    response = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_1.id}),
        {
            "type": "tmp_decorator_type_1",
            "value_provider_type": "value_provider_1",
            "value_provider_conf": {"field_id": 1},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert ViewDecoration.objects.all().count() == 1
    first = ViewDecoration.objects.all().first()
    assert response_json["id"] == first.id
    assert response_json["view"] == view_1.id
    assert response_json["type"] == first.type
    assert response_json["value_provider_type"] == first.value_provider_type
    assert response_json["value_provider_conf"] == first.value_provider_conf

    # Test default values
    response = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_1.id}),
        {"type": "tmp_decorator_type_2"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "tmp_decorator_type_2"
    assert response_json["value_provider_type"] == ""
    assert response_json["value_provider_conf"] == {}


@pytest.mark.django_db
def test_get_view_decoration(api_client, data_fixture):
    data_fixture.register_temp_decorators_and_value_providers()
    user, token = data_fixture.create_user_and_token()
    decoration_1 = data_fixture.create_view_decoration(user=user)
    decoration_2 = data_fixture.create_view_decoration()

    response = api_client.get(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_2.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        reverse(
            "api:database:views:decoration_item", kwargs={"view_decoration_id": 99999}
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DECORATION_DOES_NOT_EXIST"

    response = api_client.get(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert ViewDecoration.objects.all().count() == 2
    first = ViewDecoration.objects.get(pk=decoration_1.id)
    assert response_json["id"] == first.id
    assert response_json["view"] == first.view_id
    assert response_json["type"] == first.type
    assert response_json["value_provider_type"] == first.value_provider_type
    assert response_json["value_provider_conf"] == first.value_provider_conf
    assert response_json["order"] == first.order

    response = api_client.delete(
        reverse(
            "api:workspaces:item",
            kwargs={"workspace_id": decoration_1.view.table.database.workspace.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT

    response = api_client.get(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"


@pytest.mark.django_db
def test_update_view_decoration_validation(api_client, data_fixture):
    data_fixture.register_temp_decorators_and_value_providers()
    user, token = data_fixture.create_user_and_token()
    decoration_1 = data_fixture.create_view_decoration(user=user)
    decoration_2 = data_fixture.create_view_decoration()

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_2.id},
        ),
        {"type": "tmp_decorator_type_1"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item", kwargs={"view_decoration_id": 9999}
        ),
        {"type": "tmp_decorator_type_1"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DECORATION_DOES_NOT_EXIST"

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {"type": "bad_type"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"] == {
        "type": [
            {"error": '"bad_type" is not a valid choice.', "code": "invalid_choice"}
        ]
    }

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {"type": "tmp_decorator_type_1", "value_provider_type": "bad_type"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"] == {
        "value_provider_type": [
            {"error": '"bad_type" is not a valid choice.', "code": "invalid_choice"}
        ]
    }

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {
            "value_provider_type": "value_provider_2",
            "value_provider_conf": {"test": True},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"] == {
        "value_provider_conf": {
            "description": [{"error": "This field is required.", "code": "required"}]
        }
    }

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {
            "value_provider_type": "value_provider_2",
            "value_provider_conf": {
                "test": "should be ignored",
                "field": [{"filters": []}],
            },
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"] == {
        "value_provider_conf": {
            "description": [{"error": "This field is required.", "code": "required"}]
        }
    }


@pytest.mark.django_db
def test_update_view_decoration_to_incompatible_type(api_client, data_fixture):
    data_fixture.register_temp_decorators_and_value_providers()
    user, token = data_fixture.create_user_and_token()
    decoration_1 = data_fixture.create_view_decoration(user=user)

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {"type": "tmp_decorator_type_3"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert (
        response_json["error"] == "ERROR_VIEW_DECORATION_VALUE_PROVIDER_NOT_COMPATIBLE"
    )


@pytest.mark.django_db
def test_update_view_decoration_to_compatible_type(api_client, data_fixture):
    data_fixture.register_temp_decorators_and_value_providers()
    user, token = data_fixture.create_user_and_token()
    decoration_1 = data_fixture.create_view_decoration(user=user)

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {"type": "tmp_decorator_type_2"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    first = ViewDecoration.objects.get(pk=decoration_1.id)
    assert first.type == "tmp_decorator_type_2"
    assert first.value_provider_type == "value_provider_1"
    assert first.value_provider_conf == {}
    assert response_json["id"] == first.id
    assert response_json["view"] == first.view_id
    assert response_json["type"] == first.type
    assert response_json["value_provider_type"] == first.value_provider_type
    assert response_json["value_provider_conf"] == first.value_provider_conf
    assert response_json["order"] == first.order


@pytest.mark.django_db
def test_update_view_decoration_value_provider(api_client, data_fixture):
    data_fixture.register_temp_decorators_and_value_providers()
    user, token = data_fixture.create_user_and_token()
    decoration_1 = data_fixture.create_view_decoration(
        user=user, type="tmp_decorator_type_2"
    )

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {
            "value_provider_type": "value_provider_2",
            "value_provider_conf": {
                "description": "test",
            },
            "order": 25,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert ViewDecoration.objects.all().count() == 1
    first = ViewDecoration.objects.get(pk=decoration_1.id)
    assert first.type == "tmp_decorator_type_2"
    assert first.value_provider_type == "value_provider_2"
    assert first.value_provider_conf == {"description": "test"}
    assert first.order == 25
    assert response_json["id"] == first.id
    assert response_json["view"] == first.view_id
    assert response_json["type"] == first.type
    assert response_json["value_provider_type"] == first.value_provider_type
    assert response_json["value_provider_conf"] == first.value_provider_conf
    assert response_json["order"] == first.order

    # Change it back the type and expect the value provider to be the same.
    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {"type": "tmp_decorator_type_1"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    first = ViewDecoration.objects.get(pk=decoration_1.id)

    assert first.type == "tmp_decorator_type_1"
    assert first.value_provider_type == "value_provider_2"
    assert first.value_provider_conf == {"description": "test"}
    assert first.order == 25
    assert response_json["id"] == first.id
    assert response_json["view"] == first.view_id
    assert response_json["type"] == first.type
    assert response_json["value_provider_type"] == first.value_provider_type
    assert response_json["value_provider_conf"] == first.value_provider_conf
    assert response_json["order"] == first.order


@pytest.mark.django_db
def test_update_view_decoration_incompatible_value_provider_conf(
    api_client, data_fixture
):
    data_fixture.register_temp_decorators_and_value_providers()
    user, token = data_fixture.create_user_and_token()
    decoration_1 = data_fixture.create_view_decoration(
        user=user,
        type="tmp_decorator_type_1",
        value_provider_type="value_provider_2",
        value_provider_conf={"description": "test"},
    )

    # Change provider type with an incompatible configuration
    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {
            "value_provider_type": "value_provider_1",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"] == {
        "value_provider_conf": {
            "field_id": [{"error": "This field is required.", "code": "required"}]
        }
    }

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {
            "value_provider_type": "value_provider_1",
            "value_provider_conf": {"field_id": None},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    first = ViewDecoration.objects.get(pk=decoration_1.id)

    assert first.value_provider_type == "value_provider_1"
    assert first.value_provider_conf == {"field_id": None}
    assert response_json["value_provider_type"] == first.value_provider_type
    assert response_json["value_provider_conf"] == first.value_provider_conf

    # Remove value provider type
    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {"value_provider_conf": {"field_id": 3}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {"value_provider_type": ""},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"] == {
        "value_provider_conf": [
            {"error": "This field should be an empty object.", "code": "invalid"}
        ]
    }

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {"value_provider_type": "", "value_provider_conf": {}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    first = ViewDecoration.objects.get(pk=decoration_1.id)

    assert first.type == "tmp_decorator_type_1"
    assert first.value_provider_type == ""
    assert first.value_provider_conf == {}
    assert response_json["type"] == first.type
    assert response_json["value_provider_type"] == first.value_provider_type
    assert response_json["value_provider_conf"] == first.value_provider_conf


@pytest.mark.django_db
def test_update_view_decoration_order(api_client, data_fixture):
    data_fixture.register_temp_decorators_and_value_providers()
    user, token = data_fixture.create_user_and_token()
    decoration_1 = data_fixture.create_view_decoration(
        user=user,
        type="tmp_decorator_type_1",
        value_provider_type="value_provider_2",
        value_provider_conf={"description": "test"},
    )

    response = api_client.patch(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        {"order": 42},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    first = ViewDecoration.objects.get(pk=decoration_1.id)

    assert first.order == 42
    assert response_json["order"] == first.order


@pytest.mark.django_db
def test_delete_view_decoration(api_client, data_fixture):
    data_fixture.register_temp_decorators_and_value_providers()
    user, token = data_fixture.create_user_and_token()
    decoration_1 = data_fixture.create_view_decoration(user=user)
    decoration_2 = data_fixture.create_view_decoration()

    response = api_client.delete(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_2.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.delete(
        reverse(
            "api:database:views:decoration_item", kwargs={"view_decoration_id": 9999}
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DECORATION_DOES_NOT_EXIST"

    response = api_client.delete(
        reverse(
            "api:database:views:decoration_item",
            kwargs={"view_decoration_id": decoration_1.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 204
    assert ViewDecoration.objects.all().count() == 1


@pytest.mark.django_db
def test_list_views_including_decorations(api_client, data_fixture):
    data_fixture.register_temp_decorators_and_value_providers()
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    view_1 = data_fixture.create_grid_view(table=table_1, order=1)
    view_2 = data_fixture.create_grid_view(table=table_1, order=2)
    view_3 = data_fixture.create_grid_view(table=table_2, order=1)
    decoration_1 = data_fixture.create_view_decoration(view=view_1, order=0)
    decoration_2 = data_fixture.create_view_decoration(
        view=view_1, type="tmp_decorator_type_2", order=1
    )
    decoration_3 = data_fixture.create_view_decoration(view=view_2)
    data_fixture.create_view_decoration(view=view_3, type="tmp_decorator_type_2")

    response = api_client.get(
        "{}".format(
            reverse("api:database:views:list", kwargs={"table_id": table_1.id})
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 2
    assert "decorations" not in response_json[0]
    assert "decorations" not in response_json[1]

    response = api_client.get(
        "{}?include=decorations".format(
            reverse("api:database:views:list", kwargs={"table_id": table_1.id})
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert len(response_json[0]["decorations"]) == 2

    assert response_json[0]["decorations"][0]["id"] == decoration_1.id
    assert response_json[0]["decorations"][0]["view"] == view_1.id
    assert response_json[0]["decorations"][0]["type"] == decoration_1.type
    assert (
        response_json[0]["decorations"][0]["value_provider_type"]
        == decoration_1.value_provider_type
    )
    assert response_json[0]["decorations"][1]["id"] == decoration_2.id
    assert len(response_json[1]["decorations"]) == 1
    assert response_json[1]["decorations"][0]["id"] == decoration_3.id

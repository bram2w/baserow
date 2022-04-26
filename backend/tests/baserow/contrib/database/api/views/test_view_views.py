import pytest
from unittest.mock import patch

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from django.shortcuts import reverse
from django.contrib.contenttypes.models import ContentType

from baserow.contrib.database.views.models import View, GridView
from baserow.contrib.database.views.registries import (
    view_type_registry,
)
from baserow.contrib.database.views.view_types import GridViewType


@pytest.mark.django_db
def test_list_views(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    view_1 = data_fixture.create_grid_view(table=table_1, order=1)
    view_2 = data_fixture.create_grid_view(table=table_1, order=3)
    view_3 = data_fixture.create_grid_view(
        table=table_1, order=2, filter_type="OR", filters_disabled=True
    )
    data_fixture.create_grid_view(table=table_2, order=1)

    response = api_client.get(
        reverse("api:database:views:list", kwargs={"table_id": table_1.id}),
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert len(response_json) == 3

    assert response_json[0]["id"] == view_1.id
    assert response_json[0]["type"] == "grid"
    assert response_json[0]["filter_type"] == "AND"
    assert response_json[0]["filters_disabled"] is False

    assert response_json[1]["id"] == view_3.id
    assert response_json[1]["type"] == "grid"
    assert response_json[1]["filter_type"] == "OR"
    assert response_json[1]["filters_disabled"] is True

    assert response_json[2]["id"] == view_2.id
    assert response_json[2]["type"] == "grid"
    assert response_json[2]["filter_type"] == "AND"
    assert response_json[2]["filters_disabled"] is False

    response = api_client.get(
        reverse("api:database:views:list", kwargs={"table_id": table_2.id}),
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        reverse("api:database:views:list", kwargs={"table_id": 999999}),
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    url = reverse("api:database:views:list", kwargs={"table_id": table_1.id})
    response = api_client.get(url)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    data_fixture.create_template(group=table_1.database.group)
    url = reverse("api:database:views:list", kwargs={"table_id": table_1.id})
    response = api_client.get(url)
    assert response.status_code == HTTP_200_OK

    response = api_client.delete(
        reverse("api:groups:item", kwargs={"group_id": table_1.database.group.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT

    url = reverse("api:database:views:list", kwargs={"table_id": table_1.id})
    response = api_client.get(url)
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_get_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user_2)
    view = data_fixture.create_grid_view(table=table)
    view_2 = data_fixture.create_grid_view(table=table_2)
    view_filter = data_fixture.create_view_filter(view=view)

    url = reverse("api:database:views:item", kwargs={"view_id": view_2.id})
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:views:item", kwargs={"view_id": 99999})
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_404_NOT_FOUND

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == view.id
    assert response_json["table_id"] == view.table_id
    assert response_json["type"] == "grid"
    assert response_json["table"]["id"] == table.id
    assert response_json["filter_type"] == "AND"
    assert not response_json["filters_disabled"]
    assert "filters" not in response_json
    assert "sortings" not in response_json
    assert "decorations" not in response_json

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.get(
        "{}?include=filters,sortings,decorations".format(url),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == view.id
    assert len(response_json["filters"]) == 1
    assert response_json["filters"][0]["id"] == view_filter.id
    assert response_json["filters"][0]["view"] == view_filter.view_id
    assert response_json["filters"][0]["field"] == view_filter.field_id
    assert response_json["filters"][0]["type"] == view_filter.type
    assert response_json["filters"][0]["value"] == view_filter.value
    assert response_json["sortings"] == []
    assert response_json["decorations"] == []

    response = api_client.delete(
        reverse("api:groups:item", kwargs={"group_id": view.table.database.group.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.get(
        url,
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_delete_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user_2)
    view = data_fixture.create_grid_view(table=table)
    view_2 = data_fixture.create_grid_view(table=table_2)

    url = reverse("api:database:views:item", kwargs={"view_id": view_2.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:views:item", kwargs={"view_id": 99999})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == 204

    assert GridView.objects.all().count() == 1


@pytest.mark.django_db
def test_order_views(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    view_1 = data_fixture.create_grid_view(table=table_1, order=1)
    view_2 = data_fixture.create_grid_view(table=table_1, order=2)
    view_3 = data_fixture.create_grid_view(table=table_1, order=3)

    response = api_client.post(
        reverse("api:database:views:order", kwargs={"table_id": table_2.id}),
        {"view_ids": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.post(
        reverse("api:database:views:order", kwargs={"table_id": 999999}),
        {"view_ids": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    response = api_client.post(
        reverse("api:database:views:order", kwargs={"table_id": table_1.id}),
        {"view_ids": [0]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_VIEW_NOT_IN_TABLE"

    response = api_client.post(
        reverse("api:database:views:order", kwargs={"table_id": table_1.id}),
        {"view_ids": ["test"]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    response = api_client.post(
        reverse("api:database:views:order", kwargs={"table_id": table_1.id}),
        {"view_ids": [view_3.id, view_2.id, view_1.id]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT

    view_1.refresh_from_db()
    view_2.refresh_from_db()
    view_3.refresh_from_db()
    assert view_1.order == 3
    assert view_2.order == 2
    assert view_3.order == 1


@pytest.mark.django_db
def test_get_view_field_options(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    grid = data_fixture.create_grid_view(table=table)
    grid_2 = data_fixture.create_grid_view()

    class GridViewWithNormalViewModel(GridViewType):
        field_options_serializer_class = None

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.get(
        url,
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["field_options"]) == 0

    url = reverse("api:database:views:field_options", kwargs={"view_id": 999999})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid_2.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    with patch.dict(
        view_type_registry.registry, {"grid": GridViewWithNormalViewModel()}
    ):
        url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
        response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_SUPPORT_FIELD_OPTIONS"


@pytest.mark.django_db
def test_patch_view_field_options(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    grid = data_fixture.create_grid_view(table=table)
    grid_2 = data_fixture.create_grid_view()

    class GridViewWithoutFieldOptions(GridViewType):
        model_class = View

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(
        url,
        {"field_options": {}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["field_options"]) == 0

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
        {"field_options": {99999: {}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_UNRELATED_FIELD"

    url = reverse("api:database:views:field_options", kwargs={"view_id": 999999})
    response = api_client.patch(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid_2.id})
    response = api_client.patch(
        url,
        {"field_options": {}},
        format="json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    # This test should be last because we change the content type of the grid view.
    with patch.dict(
        view_type_registry.registry, {"grid": GridViewWithoutFieldOptions()}
    ):
        grid.content_type = ContentType.objects.get(app_label="database", model="view")
        grid.save()
        url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
        response = api_client.patch(
            url,
            {"field_options": {}},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        response_json = response.json()
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response_json["error"] == "ERROR_VIEW_DOES_NOT_SUPPORT_FIELD_OPTIONS"


@pytest.mark.django_db
def test_rotate_slug(api_client, data_fixture):
    class UnShareableViewType(GridViewType):
        can_share = False

    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    view = data_fixture.create_form_view(table=table)
    view_2 = data_fixture.create_form_view(public=True)
    grid_view = data_fixture.create_grid_view(user=user, table=table)
    old_slug = str(view.slug)

    url = reverse("api:database:views:rotate_slug", kwargs={"view_id": view_2.id})
    response = api_client.post(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    with patch.dict(view_type_registry.registry, {"grid": UnShareableViewType()}):
        url = reverse(
            "api:database:views:rotate_slug", kwargs={"view_id": grid_view.id}
        )
        response = api_client.post(
            url, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.json()["error"] == "ERROR_CANNOT_SHARE_VIEW_TYPE"

    url = reverse("api:database:views:rotate_slug", kwargs={"view_id": 99999})
    response = api_client.post(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_404_NOT_FOUND

    url = reverse("api:database:views:rotate_slug", kwargs={"view_id": view.id})
    response = api_client.post(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["slug"] != old_slug
    assert len(response_json["slug"]) == 43

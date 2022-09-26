from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.shortcuts import reverse
from django.test.utils import CaptureQueriesContext

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.views.models import GridView, View
from baserow.contrib.database.views.registries import view_type_registry
from baserow.contrib.database.views.view_types import GridViewType
from baserow.core.trash.handler import TrashHandler


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
def test_list_views_with_limit(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table_1 = data_fixture.create_database_table(user=user)
    view_1 = data_fixture.create_grid_view(table=table_1, order=1)
    data_fixture.create_grid_view(table=table_1, order=3)

    response = api_client.get(
        reverse("api:database:views:list", kwargs={"table_id": table_1.id}),
        {"limit": 1},
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]["id"] == view_1.id


@pytest.mark.django_db
def test_list_views_with_type_filter(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table_1 = data_fixture.create_database_table(user=user)
    grid = data_fixture.create_grid_view(table=table_1, order=1)
    gallery = data_fixture.create_gallery_view(table=table_1, order=2)

    response = api_client.get(
        reverse("api:database:views:list", kwargs={"table_id": table_1.id}),
        {"type": "grid"},
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]["id"] == grid.id

    response = api_client.get(
        reverse("api:database:views:list", kwargs={"table_id": table_1.id}),
        {"type": "gallery"},
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]["id"] == gallery.id


@pytest.mark.django_db
def test_list_views_doesnt_do_n_queries(api_client, data_fixture):
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

    with CaptureQueriesContext(connection) as query_for_n:
        response = api_client.get(
            reverse("api:database:views:list", kwargs={"table_id": table_1.id}),
            **{"HTTP_AUTHORIZATION": f"JWT {token}"},
        )
        assert response.status_code == HTTP_200_OK
        response_json = response.json()

    view_4 = data_fixture.create_grid_view(table=table_1, order=3)

    with CaptureQueriesContext(connection) as query_for_n_plus_one:
        response = api_client.get(
            reverse("api:database:views:list", kwargs={"table_id": table_1.id}),
            **{"HTTP_AUTHORIZATION": f"JWT {token}"},
        )
        assert response.status_code == HTTP_200_OK
        response_json = response.json()

    assert len(query_for_n.captured_queries) == len(
        query_for_n_plus_one.captured_queries
    )


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
def test_duplicate_views(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table_1 = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table_1)
    table_2 = data_fixture.create_database_table()
    view_1 = data_fixture.create_grid_view(table=table_1, order=1)
    view_2 = data_fixture.create_grid_view(table=table_2, order=2)
    view_3 = data_fixture.create_grid_view(table=table_1, order=3)

    field_option = data_fixture.create_grid_view_field_option(
        grid_view=view_1,
        field=field,
        aggregation_type="whatever",
        aggregation_raw_type="empty",
    )
    view_filter = data_fixture.create_view_filter(
        view=view_1, field=field, value="test", type="equal"
    )
    view_sort = data_fixture.create_view_sort(view=view_1, field=field, order="ASC")

    view_decoration = data_fixture.create_view_decoration(
        view=view_1,
        value_provider_conf={"config": 12},
    )

    response = api_client.post(
        reverse("api:database:views:duplicate", kwargs={"view_id": view_2.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.post(
        reverse("api:database:views:duplicate", kwargs={"view_id": 999999}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    assert View.objects.count() == 3

    response = api_client.post(
        reverse("api:database:views:duplicate", kwargs={"view_id": view_1.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert View.objects.count() == 4

    assert response_json["id"] != view_1.id
    assert response_json["order"] == view_1.order + 1
    assert "sortings" in response_json
    assert "filters" in response_json
    assert "decorations" in response_json


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
def test_get_view_field_options_as_template(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    grid = data_fixture.create_grid_view(table=table)

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.get(url)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    data_fixture.create_template(group=grid.table.database.group)
    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.get(url)
    assert response.status_code == HTTP_200_OK


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
def test_patch_view_field_options_as_template(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    grid = data_fixture.create_grid_view(table=table)

    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(url)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    data_fixture.create_template(group=grid.table.database.group)
    url = reverse("api:database:views:field_options", kwargs={"view_id": grid.id})
    response = api_client.patch(url)
    assert response.status_code == HTTP_401_UNAUTHORIZED


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


@pytest.mark.django_db
def test_anon_user_cant_get_info_about_a_non_public_view(api_client, data_fixture):
    user = data_fixture.create_user()
    grid_view = data_fixture.create_grid_view(user=user, public=False)

    # Get access as an anonymous user
    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": grid_view.slug})
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json == {
        "detail": "The requested view does not exist.",
        "error": "ERROR_VIEW_DOES_NOT_EXIST",
    }


@pytest.mark.django_db
def test_user_in_wrong_group_cant_get_info_about_a_non_public_view(
    api_client, data_fixture
):
    user = data_fixture.create_user()
    other_user, other_user_token = data_fixture.create_user_and_token()
    grid_view = data_fixture.create_grid_view(user=user, public=False)

    response = api_client.get(
        reverse(
            "api:database:views:public_info",
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
def test_user_in_same_group_can_get_info_about_a_non_public_view(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    grid_view = data_fixture.create_grid_view(user=user, public=False)

    response = api_client.get(
        reverse(
            "api:database:views:public_info",
            kwargs={"slug": grid_view.slug},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK, response_json
    assert "fields" in response_json
    assert "view" in response_json


@pytest.mark.django_db
def test_cannot_get_info_about_not_eligibile_view_type(api_client, data_fixture):
    user = data_fixture.create_user()
    form_view = data_fixture.create_form_view(user=user, public=True)

    # Get access as an anonymous user
    response = api_client.get(
        reverse(
            "api:database:views:public_info",
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
def test_cannot_get_info_about_trashed_view(api_client, data_fixture):
    user = data_fixture.create_user()
    grid_view = data_fixture.create_grid_view(user=user, public=True)

    TrashHandler.trash(
        user, grid_view.table.database.group, None, grid_view.table.database.group
    )

    response = api_client.get(
        reverse(
            "api:database:views:public_info",
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
def test_anon_user_cant_get_info_about_a_public_password_protected_view(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    grid_view = data_fixture.create_grid_view(user=user, public=True)

    # set password for the current view using the API
    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": grid_view.id}),
        {"public_view_password": "12345678"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    # Get access as an anonymous user
    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": grid_view.slug})
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    response_json = response.json()
    public_view_token = response_json.get("access_token", None)
    assert public_view_token is None


@pytest.mark.django_db
def test_user_with_invalid_token_cant_get_info_about_a_public_password_protected_view(
    api_client, data_fixture
):
    user = data_fixture.create_user()
    grid_view = data_fixture.create_public_password_protected_grid_view(
        user=user, password="12345678"
    )

    # can't get info about the view
    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": grid_view.slug}),
        format="json",
        HTTP_BASEROW_VIEW_AUTHORIZATION=f"JWT token",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_user_with_password_can_get_info_about_a_public_password_protected_view(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    password = "12345678"
    grid_view = data_fixture.create_public_password_protected_grid_view(
        user=user, password=password
    )

    # The body of the request must contains a password field
    response = api_client.post(
        reverse("api:database:views:public_auth", kwargs={"slug": grid_view.slug}),
        {"wrong_body_param": password},
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    # Get the authorization token
    response = api_client.post(
        reverse("api:database:views:public_auth", kwargs={"slug": grid_view.slug}),
        {"password": password},
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    public_view_token = response_json.get("access_token", None)
    assert public_view_token is not None

    # Get access as with the authorization token
    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": grid_view.slug}),
        format="json",
        HTTP_BASEROW_VIEW_AUTHORIZATION=f"JWT {public_view_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "fields": [],
        "view": {
            "id": grid_view.slug,
            "name": grid_view.name,
            "order": 0,
            "public": True,
            "slug": grid_view.slug,
            "sortings": [],
            "table": {
                "database_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                "id": PUBLIC_PLACEHOLDER_ENTITY_ID,
            },
            "type": "grid",
            "row_identifier_type": grid_view.row_identifier_type,
            "show_logo": grid_view.show_logo,
        },
    }

    # The original user can still access data
    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": grid_view.slug}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "fields": [],
        "view": {
            "id": grid_view.slug,
            "name": grid_view.name,
            "order": 0,
            "public": True,
            "slug": grid_view.slug,
            "sortings": [],
            "table": {
                "database_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                "id": PUBLIC_PLACEHOLDER_ENTITY_ID,
            },
            "type": "grid",
            "row_identifier_type": grid_view.row_identifier_type,
            "show_logo": grid_view.show_logo,
        },
    }


@pytest.mark.django_db
def test_rotating_slug_of_a_public_password_protected_view_invalidate_previous_tokens(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    (
        grid_view,
        public_view_token,
    ) = data_fixture.create_public_password_protected_grid_view_with_token(
        user=user, password="12345678"
    )

    # rotating slug invalidate previous tokens
    response = api_client.post(
        reverse("api:database:views:rotate_slug", kwargs={"view_id": grid_view.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["id"] == grid_view.id
    new_slug = response_json["slug"]
    assert new_slug != grid_view.slug

    # Cannot access data anymore with the initial token
    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": new_slug}),
        format="json",
        HTTP_BASEROW_VIEW_AUTHORIZATION=f"JWT {public_view_token}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_view_creator_can_always_get_data_of_a_public_password_protected(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    password = "12345678"
    grid_view = data_fixture.create_public_password_protected_grid_view(
        user=user, password=password
    )

    # anon user cannot access
    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": grid_view.slug}),
        format="json",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # user in a valid group can access data, event without password
    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": grid_view.slug}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_user_in_wrong_group_need_the_password_to_access_password_protected_view(
    api_client, data_fixture
):
    user = data_fixture.create_user()
    _, other_user_token = data_fixture.create_user_and_token()

    (
        grid_view,
        public_view_token,
    ) = data_fixture.create_public_password_protected_grid_view_with_token(
        user=user, password="12345678"
    )

    # user2 cannot access data
    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": grid_view.slug}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {other_user_token}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # Get access as with the authorization token
    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": grid_view.slug}),
        format="json",
        HTTP_BASEROW_VIEW_AUTHORIZATION=f"JWT {public_view_token}",
        HTTP_AUTHORIZATION=f"JWT {other_user_token}",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_public_gallery_view_fields_include_cover_image(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(user=user, table=table)
    gallery_view = data_fixture.create_gallery_view(
        user=user, table=table, public=True, card_cover_image_field=file_field
    )
    data_fixture.create_gallery_view_field_option(gallery_view, file_field, hidden=True)

    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": gallery_view.slug}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["fields"]) == 1


@pytest.mark.django_db
def test_view_cant_update_show_logo(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    view = data_fixture.create_grid_view(user=user, table=table, show_logo=True)
    data = {"show_logo": False}

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": view.id}),
        data,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    view.refresh_from_db()
    assert view.show_logo is True

    response_data = response.json()
    assert response_data["show_logo"] is True

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from django.shortcuts import reverse
from django.test import override_settings

import pytest
from freezegun import freeze_time
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.actions import UpdateRowsActionType
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.search.handler import ALL_SEARCH_MODES, SearchHandler
from baserow.contrib.database.table.cache import invalidate_table_in_model_cache
from baserow.contrib.database.tokens.handler import TokenHandler
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.test_utils.helpers import (
    AnyInt,
    assert_undo_redo_actions_are_valid,
    setup_interesting_test_table,
)


@pytest.mark.django_db
def test_list_rows(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    field_1 = data_fixture.create_text_field(name="Name", table=table, primary=True)
    field_2 = data_fixture.create_number_field(name="Price", table=table)
    field_3 = data_fixture.create_text_field()
    field_4 = data_fixture.create_boolean_field(name="InStock", table=table)
    grid_view = data_fixture.create_grid_view(user=user, table=table)
    unrelated_view = data_fixture.create_grid_view(user=user, table=table_2)
    data_fixture.create_view_filter(
        view=grid_view, user=user, field=field_1, value="Product 1"
    )

    token = TokenHandler().create_token(user, table.database.workspace, "Good")
    wrong_token = TokenHandler().create_token(user, table.database.workspace, "Wrong")
    TokenHandler().update_token_permissions(user, wrong_token, True, False, True, True)

    model = table.get_model(attribute_names=True)
    row_1 = model.objects.create(name="Product 1", price=50, order=Decimal("1"))
    row_2 = model.objects.create(name="Product 2/3", price=100, order=Decimal("2"))
    row_3 = model.objects.create(name="Product 3", price=150, order=Decimal("3"))
    row_4 = model.objects.create(name="Last product", price=200, order=Decimal("4"))

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": 999999}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table_2.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION="Token abc123",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_TOKEN_DOES_NOT_EXIST"

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"Token {wrong_token.key}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_NO_PERMISSION_TO_TABLE"

    user.is_active = False
    user.save()
    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_USER_NOT_ACTIVE"
    user.is_active = True
    user.save()

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert len(response_json["results"]) == 4
    assert response_json["results"][0]["id"] == row_1.id
    assert response_json["results"][0][f"field_{field_1.id}"] == "Product 1"
    assert response_json["results"][0][f"field_{field_2.id}"] == "50"
    assert response_json["results"][0]["order"] == "1.00000000000000000000"

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?include=field_{field_1.id},field_{field_3.id}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert f"field_{field_1.id}" in response_json["results"][0]
    assert f"field_{field_2.id}" not in response_json["results"][0]
    assert f"field_{field_3.id}" not in response_json["results"][0]

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?exclude=field_{field_1.id}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert f"field_{field_1.id}" not in response_json["results"][0]
    assert f"field_{field_2.id}" in response_json["results"][0]

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?size=2&page=1", format="json", HTTP_AUTHORIZATION=f"JWT {jwt_token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert len(response_json["results"]) == 2
    assert response_json["results"][0]["id"] == row_1.id
    assert response_json["results"][1]["id"] == row_2.id

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?size=2&page=2", format="json", HTTP_AUTHORIZATION=f"JWT {jwt_token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert len(response_json["results"]) == 2
    assert response_json["results"][0]["id"] == row_3.id
    assert response_json["results"][1]["id"] == row_4.id

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?size=2&page=3", format="json", HTTP_AUTHORIZATION=f"JWT {jwt_token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_INVALID_PAGE"

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?size=201", format="json", HTTP_AUTHORIZATION=f"JWT {jwt_token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_PAGE_SIZE_LIMIT"

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?search=Product 1", format="json", HTTP_AUTHORIZATION=f"JWT {jwt_token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_1.id

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?search=4", format="json", HTTP_AUTHORIZATION=f"JWT {jwt_token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_4.id

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?search=3", format="json", HTTP_AUTHORIZATION=f"JWT {jwt_token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 2
    assert len(response_json["results"]) == 2
    assert response_json["results"][0]["id"] == row_2.id
    assert response_json["results"][1]["id"] == row_3.id

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?search=200", format="json", HTTP_AUTHORIZATION=f"JWT {jwt_token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_4.id

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?order_by=field_999999",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_ORDER_BY_FIELD_NOT_FOUND"
    assert response_json["detail"] == (
        "The field field_999999 was not found in the table."
    )

    number_field_type = field_type_registry.get("number")
    old_can_order_by = number_field_type._can_order_by
    number_field_type._can_order_by = False
    invalidate_table_in_model_cache(table.id)
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?order_by=-field_{field_2.id}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_ORDER_BY_FIELD_NOT_POSSIBLE"
    assert response_json["detail"] == (
        f"It is not possible to order by field_{field_2.id} because the field type "
        f"number does not support filtering."
    )
    number_field_type._can_order_by = old_can_order_by
    invalidate_table_in_model_cache(table.id)

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?order_by=-field_{field_2.id}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert len(response_json["results"]) == 4
    assert response_json["results"][0]["id"] == row_4.id
    assert response_json["results"][1]["id"] == row_3.id
    assert response_json["results"][2]["id"] == row_2.id
    assert response_json["results"][3]["id"] == row_1.id

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    get_params = [f"filter__field_9999999__contains=last"]
    response = api_client.get(
        f'{url}?{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_FILTER_FIELD_NOT_FOUND"

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    get_params = [f"filter__field_{field_4.id}__contains=100"]
    response = api_client.get(
        f'{url}?{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD"

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    get_params = [f"filter__field_{field_2.id}__INVALID=100"]
    response = api_client.get(
        f'{url}?{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST"
    assert response_json["detail"] == "The view filter type INVALID doesn't exist."

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    get_params = [
        f"filter__field_{field_1.id}__contains=last",
        f"filter__field_{field_2.id}__equal=200",
    ]
    response = api_client.get(
        f'{url}?{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_4.id

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    get_params = [
        f"filter__field_{field_1.id}__contains=last",
        f"filter__field_{field_2.id}__higher_than=110",
        "filter_type=or",
    ]
    response = api_client.get(
        f'{url}?{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 2
    assert len(response_json["results"]) == 2
    assert response_json["results"][0]["id"] == row_3.id
    assert response_json["results"][1]["id"] == row_4.id

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    get_params = [
        f"filter__field_{field_1.id}__equal=Product 1",
        f"filter__field_{field_1.id}__equal=Product 3",
        "filter_type=or",
    ]
    response = api_client.get(
        f'{url}?{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 2
    assert len(response_json["results"]) == 2
    assert response_json["results"][0]["id"] == row_1.id
    assert response_json["results"][1]["id"] == row_3.id

    row_2.order = Decimal("999")
    row_2.save()
    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 4
    assert len(response_json["results"]) == 4
    assert response_json["results"][0]["id"] == row_1.id
    assert response_json["results"][1]["id"] == row_3.id
    assert response_json["results"][2]["id"] == row_4.id
    assert response_json["results"][3]["id"] == row_2.id

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
        data={"view_id": grid_view.id},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_1.id

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
        data={"view_id": -1},
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
        data={"view_id": unrelated_view.id},
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"


@pytest.mark.django_db
def test_list_rows_adhoc_filtering_query_param_null_character(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table, name="normal")
    first_row = RowHandler().create_row(
        user, table, values={"normal": "a"}, user_field_names=True
    )
    RowHandler().create_row(user, table, values={"normal": "b"}, user_field_names=True)

    str_with_null_character = "a\0"
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    get_params = [f"filter__field_{text_field.id}__contains={str_with_null_character}"]
    response = api_client.get(
        f'{url}?{"&".join(get_params)}', HTTP_AUTHORIZATION=f"JWT {token}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == first_row.id


@pytest.mark.django_db
def test_list_rows_user_field_names(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    field_1 = data_fixture.create_text_field(name="Name", table=table, primary=True)
    field_2 = data_fixture.create_text_field(name="field_123456", table=table)
    field_3 = data_fixture.create_text_field(name="field_üńîćødë", table=table)

    model = table.get_model(attribute_names=True)
    row_1 = model.objects.create(
        name="Product 1", field123456="1st product", order=Decimal("1")
    )
    row_2 = model.objects.create(
        name="Product 2", field123456="2nd product", order=Decimal("2")
    )
    row_3 = model.objects.create(
        name="Product 3", field123456="3rd product", order=Decimal("3")
    )
    row_4 = model.objects.create(
        name="Product 4", fieldüńîćødë="Unicode product", order=Decimal("4")
    )

    # Test with field names
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    get_params = [
        f"filter__{field_1.name}__equal=Product 1",
        f"filter__{field_1.name}__equal=Product 2",
        "filter_type=or",
    ]
    response = api_client.get(
        f'{url}?user_field_names=true&{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 2
    assert len(response_json["results"]) == 2
    assert response_json["results"][0]["id"] == row_1.id
    assert response_json["results"][1]["id"] == row_2.id

    # Test with field_id and user_field_names=true
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    get_params = [
        f"filter__field_{field_1.id}__equal=Product 1",
        f"filter__field_{field_1.id}__equal=Product 2",
        "filter_type=or",
    ]
    response = api_client.get(
        f'{url}?user_field_names=true&{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 2
    assert len(response_json["results"]) == 2
    assert response_json["results"][0]["id"] == row_1.id
    assert response_json["results"][1]["id"] == row_2.id

    # Test with field name "field_123456" and user_field_names=true
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    get_params = [
        f"filter__{field_2.name}__equal=3rd product",
        "filter_type=or",
    ]
    response = api_client.get(
        f'{url}?user_field_names=true&{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_3.id

    # Test with field name "field_üńîćødë" and user_field_names=true
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    get_params = [
        f"filter__{field_3.name}__equal=Unicode product",
        "filter_type=or",
    ]
    response = api_client.get(
        f'{url}?user_field_names=true&{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_4.id


@pytest.mark.django_db
def test_list_rows_sort_query_overrides_existing_sort(data_fixture, api_client):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    field_1 = data_fixture.create_text_field(name="Name", table=table, primary=True)
    grid_view = data_fixture.create_grid_view(user=user, table=table)
    data_fixture.create_view_sort(
        user=user, view=grid_view, field=field_1, order="DESC"
    )

    model = table.get_model(attribute_names=True)
    row_1 = model.objects.create(name="a")
    row_2 = model.objects.create(name="b")
    row_3 = model.objects.create(name="c")
    row_4 = model.objects.create(name="d")

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
        data={"view_id": grid_view.id, "order_by": field_1.id},
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["results"][0]["id"] == row_1.id


@pytest.mark.django_db
def test_list_rows_filter_stacks_with_existing_filter(data_fixture, api_client):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    field_1 = data_fixture.create_text_field(name="Name", table=table, primary=True)
    field_2 = data_fixture.create_number_field(name="Number", table=table)
    grid_view = data_fixture.create_grid_view(user=user, table=table)
    data_fixture.create_view_filter(
        view=grid_view, user=user, field=field_1, value="ab", type="contains"
    )

    model = table.get_model(attribute_names=True)
    row_1 = model.objects.create(name="a", number="1")
    row_2 = model.objects.create(name="ab", number="2")
    row_3 = model.objects.create(name="abc", number="3")
    row_4 = model.objects.create(name="abcd", number="1")

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
        data={"view_id": grid_view.id, f"filter__field_{field_2.id}__contains": "1"},
    )

    # The only row that matches both filters is row_4
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_4.id


@pytest.mark.django_db
def test_list_rows_filter_filters_query_param(data_fixture, api_client):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    field_1 = data_fixture.create_text_field(name="Name", table=table, primary=True)
    field_2 = data_fixture.create_number_field(name="Number", table=table)

    model = table.get_model(attribute_names=True)
    row_1 = model.objects.create(name="a", number="1")
    row_2 = model.objects.create(name="ab", number="2")
    row_3 = model.objects.create(name="abc", number="3")
    row_4 = model.objects.create(name="abcd", number="1")

    advanced_filters = {
        "filter_type": "AND",
        "groups": [
            {
                "filter_type": "AND",
                "filters": [
                    {
                        "field": field_1.id,
                        "type": "contains",
                        "value": "a",
                    },
                    {
                        "field": field_2.id,
                        "type": "equal",
                        "value": 3,
                    },
                ],
            }
        ],
    }
    get_params = ["filters=" + json.dumps(advanced_filters)]
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})

    response = api_client.get(
        f'{url}?{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_3.id


@pytest.mark.django_db
def test_list_rows_filter_filters_query_param_with_user_field_names(
    data_fixture, api_client
):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    field_1 = data_fixture.create_text_field(name="Name", table=table, primary=True)
    field_2 = data_fixture.create_number_field(name="Number", table=table)

    model = table.get_model(attribute_names=True)
    row_1 = model.objects.create(name="a", number="1")
    row_2 = model.objects.create(name="ab", number="2")
    row_3 = model.objects.create(name="abc", number="3")
    row_4 = model.objects.create(name="abcd", number="1")

    advanced_filters = {
        "filter_type": "AND",
        "groups": [
            {
                "filter_type": "AND",
                "filters": [
                    {
                        "field": "Name",
                        "type": "contains",
                        "value": "a",
                    },
                    {
                        "field": "Number",
                        "type": "equal",
                        "value": 3,
                    },
                ],
            }
        ],
    }
    get_params = ["filters=" + json.dumps(advanced_filters), "user_field_names=true"]
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})

    response = api_client.get(
        f'{url}?{"&".join(get_params)}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == row_3.id


@pytest.mark.django_db
def test_create_row(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    text_field = data_fixture.create_text_field(
        table=table, order=0, name="Color", text_default="white"
    )
    number_field = data_fixture.create_number_field(
        table=table, order=1, name="Horsepower"
    )
    boolean_field = data_fixture.create_boolean_field(
        table=table, order=2, name="For sale"
    )
    text_field_2 = data_fixture.create_text_field(
        table=table, order=3, name="Description"
    )

    token = TokenHandler().create_token(user, table.database.workspace, "Good")
    wrong_token = TokenHandler().create_token(user, table.database.workspace, "Wrong")
    TokenHandler().update_token_permissions(user, wrong_token, False, True, True, True)

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": 99999}),
        {f"field_{text_field.id}": "Test 1"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{text_field.id}": "Test 1"},
        format="json",
        HTTP_AUTHORIZATION="Token abc123",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_TOKEN_DOES_NOT_EXIST"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{text_field.id}": "Test 1"},
        format="json",
        HTTP_AUTHORIZATION=f"Token {wrong_token.key}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_NO_PERMISSION_TO_TABLE"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table_2.id}),
        {f"field_{text_field.id}": "Green"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.post(
        f"{url}?before=99999",
        {f"field_{text_field.id}": "Green"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ROW_DOES_NOT_EXIST"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{text_field.id}": "Green",
            f"field_{number_field.id}": -10,
            f"field_{boolean_field.id}": None,
            f"field_{text_field_2.id}": None,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert len(response_json["detail"]) == 2
    assert response_json["detail"][f"field_{number_field.id}"][0]["code"] == "min_value"
    assert response_json["detail"][f"field_{boolean_field.id}"][0]["code"] == "null"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json_row_1 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_1[f"field_{text_field.id}"] == "white"
    assert not response_json_row_1[f"field_{number_field.id}"]
    assert response_json_row_1[f"field_{boolean_field.id}"] is False
    assert response_json_row_1[f"field_{text_field_2.id}"] is None
    assert response_json_row_1["order"] == "1.00000000000000000000"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{number_field.id}": None,
            f"field_{boolean_field.id}": False,
            f"field_{text_field_2.id}": "",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json_row_2 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_2[f"field_{text_field.id}"] == "white"
    assert not response_json_row_2[f"field_{number_field.id}"]
    assert response_json_row_2[f"field_{boolean_field.id}"] is False
    assert response_json_row_2[f"field_{text_field_2.id}"] == ""
    assert response_json_row_2["order"] == "2.00000000000000000000"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{text_field.id}": "Green",
            f"field_{number_field.id}": 120,
            f"field_{boolean_field.id}": True,
            f"field_{text_field_2.id}": "Not important",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json_row_3 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_3[f"field_{text_field.id}"] == "Green"
    assert response_json_row_3[f"field_{number_field.id}"] == "120"
    assert response_json_row_3[f"field_{boolean_field.id}"]
    assert response_json_row_3[f"field_{text_field_2.id}"] == "Not important"
    assert response_json_row_3["order"] == "3.00000000000000000000"

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"field_{text_field.id}": "Purple",
            f"field_{number_field.id}": 240,
            f"field_{boolean_field.id}": True,
            f"field_{text_field_2.id}": "",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )
    response_json_row_4 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_4[f"field_{text_field.id}"] == "Purple"
    assert response_json_row_4[f"field_{number_field.id}"] == "240"
    assert response_json_row_4[f"field_{boolean_field.id}"]
    assert response_json_row_4[f"field_{text_field_2.id}"] == ""
    assert response_json_row_4["order"] == "4.00000000000000000000"

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.post(
        f"{url}?before={response_json_row_3['id']}",
        {
            f"field_{text_field.id}": "Red",
            f"field_{number_field.id}": 480,
            f"field_{boolean_field.id}": False,
            f"field_{text_field_2.id}": "",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )
    response_json_row_5 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_5[f"field_{text_field.id}"] == "Red"
    assert response_json_row_5[f"field_{number_field.id}"] == "480"
    assert not response_json_row_5[f"field_{boolean_field.id}"]
    assert response_json_row_5[f"field_{text_field_2.id}"] == ""
    assert response_json_row_5["order"] == "2.50000000000000000000"

    model = table.get_model()
    assert model.objects.all().count() == 5
    rows = model.objects.all()

    row_1, row_2, row_5, row_3, row_4 = rows

    assert row_1.id == response_json_row_1["id"]
    assert getattr(row_1, f"field_{text_field.id}") == "white"
    assert getattr(row_1, f"field_{number_field.id}") is None
    assert getattr(row_1, f"field_{boolean_field.id}") is False
    assert getattr(row_1, f"field_{text_field_2.id}") is None

    assert row_2.id == response_json_row_2["id"]
    assert getattr(row_2, f"field_{text_field.id}") == "white"
    assert getattr(row_2, f"field_{number_field.id}") is None
    assert getattr(row_2, f"field_{boolean_field.id}") is False
    assert getattr(row_2, f"field_{text_field_2.id}") == ""

    assert row_3.id == response_json_row_3["id"]
    assert getattr(row_3, f"field_{text_field.id}") == "Green"
    assert getattr(row_3, f"field_{number_field.id}") == 120
    assert getattr(row_3, f"field_{boolean_field.id}") is True
    assert getattr(row_3, f"field_{text_field_2.id}") == "Not important"

    assert row_4.id == response_json_row_4["id"]
    assert getattr(row_4, f"field_{text_field.id}") == "Purple"
    assert getattr(row_4, f"field_{number_field.id}") == 240
    assert getattr(row_4, f"field_{boolean_field.id}") is True
    assert getattr(row_4, f"field_{text_field_2.id}") == ""

    assert row_5.id == response_json_row_5["id"]
    assert getattr(row_5, f"field_{text_field.id}") == "Red"
    assert getattr(row_5, f"field_{number_field.id}") == 480
    assert getattr(row_5, f"field_{boolean_field.id}") is False
    assert getattr(row_5, f"field_{text_field_2.id}") == ""

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})

    response = api_client.post(
        f"{url}?user_field_names=true",
        {
            f"Color": "Red",
            f"Horsepower": 480,
            f"For Sale": False,
            f"Description": "",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json == {
        "Color": "Red",
        "Description": "",
        "For sale": False,
        "Horsepower": "480",
        "id": 6,
        "order": "5.00000000000000000000",
    }

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.post(
        f"{url}?user_field_names=true",
        {
            f"INVALID FIELD NAME": "Red",
            f"Horsepower": 480,
            f"For Sale": False,
            f"Description": "",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json == {
        "Color": "white",  # Has gone to the default value when not specified.
        "Description": "",
        "For sale": False,
        "Horsepower": "480",
        "id": 7,
        "order": "6.00000000000000000000",
    }


@pytest.mark.django_db
def test_create_empty_row_for_interesting_fields(api_client, data_fixture):
    """
    Test a common case: create a row with empty values.
    """

    table, user, row, _, context = setup_interesting_test_table(data_fixture)
    jwt_token = data_fixture.generate_token(user)

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id})
        + "?user_field_names=true",
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_create_row_with_blank_decimal_field(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    decimal_field = data_fixture.create_number_field(
        table=table, order=1, name="TestDecimal", number_decimal_places=1
    )

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"field_{decimal_field.id}": ""},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    response_json_row_1 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_1[f"field_{decimal_field.id}"] is None


@pytest.mark.django_db
def test_get_row(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    text_field = data_fixture.create_text_field(
        table=table, order=0, name="Color", text_default="white"
    )
    number_field = data_fixture.create_number_field(
        table=table, order=1, name="Horsepower"
    )
    boolean_field = data_fixture.create_boolean_field(
        table=table, order=2, name="For sale"
    )

    token = TokenHandler().create_token(user, table.database.workspace, "Good")
    wrong_token = TokenHandler().create_token(user, table.database.workspace, "Wrong")
    TokenHandler().update_token_permissions(user, wrong_token, True, False, True, True)

    model = table.get_model()
    row_1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Green",
            f"field_{number_field.id}": 120,
            f"field_{boolean_field.id}": False,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Purple",
            f"field_{number_field.id}": 240,
            f"field_{boolean_field.id}": True,
        }
    )

    url = reverse("api:database:rows:item", kwargs={"table_id": 9999, "row_id": 9999})
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {jwt_token}")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table_2.id, "row_id": row_1.id}
    )
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {jwt_token}")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION="Token abc123")
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_TOKEN_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.get(
        url, format="json", HTTP_AUTHORIZATION=f"Token {wrong_token.key}"
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_NO_PERMISSION_TO_TABLE"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": 99999}
    )
    response = api_client.get(
        url,
        {f"field_{text_field.id}": "Orange"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ROW_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {jwt_token}")
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == row_1.id
    assert response_json[f"field_{text_field.id}"] == "Green"
    assert response_json[f"field_{number_field.id}"] == "120"
    assert response_json[f"field_{boolean_field.id}"] is False

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_2.id}
    )
    response = api_client.get(
        url, format="json", HTTP_AUTHORIZATION=f"Token {token.key}"
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == row_2.id
    assert response_json[f"field_{text_field.id}"] == "Purple"
    assert response_json[f"field_{number_field.id}"] == "240"
    assert response_json[f"field_{boolean_field.id}"] is True


@pytest.mark.django_db
def test_update_row(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    text_field = data_fixture.create_text_field(
        table=table, order=0, name="Color", text_default="white"
    )
    number_field = data_fixture.create_number_field(
        table=table, order=1, name="Horsepower"
    )
    boolean_field = data_fixture.create_boolean_field(
        table=table, order=2, name="For sale"
    )

    token = TokenHandler().create_token(user, table.database.workspace, "Good")
    wrong_token = TokenHandler().create_token(user, table.database.workspace, "Wrong")
    TokenHandler().update_token_permissions(user, wrong_token, True, True, False, True)

    model = table.get_model()
    row_1 = model.objects.create()
    row_2 = model.objects.create()

    url = reverse("api:database:rows:item", kwargs={"table_id": 9999, "row_id": 9999})
    response = api_client.patch(
        url,
        {f"field_{text_field.id}": "Orange"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table_2.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        url,
        {f"field_{text_field.id}": "Orange"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        url,
        {f"field_{text_field.id}": "Orange"},
        format="json",
        HTTP_AUTHORIZATION="Token abc123",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_TOKEN_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        url,
        {f"field_{text_field.id}": "Orange"},
        format="json",
        HTTP_AUTHORIZATION=f"Token {wrong_token.key}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_NO_PERMISSION_TO_TABLE"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": 99999}
    )
    response = api_client.patch(
        url,
        {f"field_{text_field.id}": "Orange"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ROW_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        url,
        {
            f"field_{text_field.id}": "Green",
            f"field_{number_field.id}": -10,
            f"field_{boolean_field.id}": None,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert len(response_json["detail"]) == 2
    assert response_json["detail"][f"field_{number_field.id}"][0]["code"] == "min_value"
    assert response_json["detail"][f"field_{boolean_field.id}"][0]["code"] == "null"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        url,
        {
            f"field_{text_field.id}": "Green",
            f"field_{number_field.id}": 120,
            f"field_{boolean_field.id}": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json_row_1 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_1["id"] == row_1.id
    assert response_json_row_1[f"field_{text_field.id}"] == "Green"
    assert response_json_row_1[f"field_{number_field.id}"] == "120"
    assert response_json_row_1[f"field_{boolean_field.id}"] is True

    row_1.refresh_from_db()
    assert getattr(row_1, f"field_{text_field.id}") == "Green"
    assert getattr(row_1, f"field_{number_field.id}") == Decimal("120")
    assert getattr(row_1, f"field_{boolean_field.id}") is True

    response = api_client.patch(
        url,
        {f"field_{text_field.id}": "Purple"},
        format="json",
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )
    response_json_row_1 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_1[f"field_{text_field.id}"] == "Purple"
    assert response_json_row_1[f"field_{number_field.id}"] == "120"
    assert response_json_row_1[f"field_{boolean_field.id}"] is True
    row_1.refresh_from_db()
    assert getattr(row_1, f"field_{text_field.id}") == "Purple"
    assert getattr(row_1, f"field_{number_field.id}") == Decimal("120")
    assert getattr(row_1, f"field_{boolean_field.id}") is True

    response = api_client.patch(
        url,
        {f"field_{text_field.id}": "Orange"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json_row_1 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_1[f"field_{text_field.id}"] == "Orange"
    assert response_json_row_1[f"field_{number_field.id}"] == "120"
    assert response_json_row_1[f"field_{boolean_field.id}"] is True
    row_1.refresh_from_db()
    assert getattr(row_1, f"field_{text_field.id}") == "Orange"
    assert getattr(row_1, f"field_{number_field.id}") == 120
    assert getattr(row_1, f"field_{boolean_field.id}") is True

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_2.id}
    )
    response = api_client.patch(
        url,
        {
            f"field_{text_field.id}": "Blue",
            f"field_{number_field.id}": 50,
            f"field_{boolean_field.id}": False,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json_row_2 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_2["id"] == row_2.id
    assert response_json_row_2[f"field_{text_field.id}"] == "Blue"
    assert response_json_row_2[f"field_{number_field.id}"] == "50"
    assert response_json_row_2[f"field_{boolean_field.id}"] is False

    row_2.refresh_from_db()
    assert getattr(row_2, f"field_{text_field.id}") == "Blue"
    assert getattr(row_2, f"field_{number_field.id}") == Decimal("50")
    assert getattr(row_2, f"field_{boolean_field.id}") is False

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_2.id}
    )
    response = api_client.patch(
        url,
        {
            f"field_{text_field.id}": None,
            f"field_{number_field.id}": None,
            f"field_{boolean_field.id}": False,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json_row_2 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_2["id"] == row_2.id
    assert response_json_row_2[f"field_{text_field.id}"] is None
    assert response_json_row_2[f"field_{number_field.id}"] is None
    assert response_json_row_2[f"field_{boolean_field.id}"] is False

    row_2.refresh_from_db()
    assert getattr(row_2, f"field_{text_field.id}") is None
    assert getattr(row_2, f"field_{number_field.id}") is None
    assert getattr(row_2, f"field_{boolean_field.id}") is False

    table_3 = data_fixture.create_database_table(user=user)
    decimal_field = data_fixture.create_number_field(
        table=table_3,
        order=0,
        name="Price",
        number_decimal_places=2,
    )
    model_3 = table_3.get_model()
    row_3 = model_3.objects.create()

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table_3.id, "row_id": row_3.id}
    )
    response = api_client.patch(
        url,
        {f"field_{decimal_field.id}": 10.22},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"field_{decimal_field.id}"] == "10.22"
    assert response_json_row_2[f"field_{number_field.id}"] is None
    assert response_json_row_2[f"field_{boolean_field.id}"] is False

    row_3.refresh_from_db()
    assert getattr(row_3, f"field_{decimal_field.id}") == Decimal("10.22")
    assert getattr(row_2, f"field_{number_field.id}") is None
    assert getattr(row_2, f"field_{boolean_field.id}") is False

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table_3.id, "row_id": row_3.id}
    )
    response = api_client.patch(
        f"{url}?user_field_names=true",
        {f"Price": 10.01},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f"Price"] == "10.01"
    assert "Horsepower" not in response_json
    assert "For sale" not in response_json

    row_3.refresh_from_db()
    assert getattr(row_3, f"field_{decimal_field.id}") == Decimal("10.01")
    assert getattr(row_2, f"field_{number_field.id}") is None
    assert getattr(row_2, f"field_{boolean_field.id}") is False


@pytest.mark.django_db
def test_move_row(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()

    token = TokenHandler().create_token(user, table.database.workspace, "Good")
    wrong_token = TokenHandler().create_token(user, table.database.workspace, "Wrong")
    TokenHandler().update_token_permissions(user, wrong_token, True, True, False, True)

    handler = RowHandler()
    row_1 = handler.create_row(user=user, table=table)
    row_2 = handler.create_row(user=user, table=table)
    row_3 = handler.create_row(user=user, table=table)

    url = reverse("api:database:rows:move", kwargs={"table_id": 9999, "row_id": 9999})
    response = api_client.patch(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:move", kwargs={"table_id": table_2.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse(
        "api:database:rows:move", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        url,
        format="json",
        HTTP_AUTHORIZATION="Token abc123",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_TOKEN_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:move", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"Token {wrong_token.key}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_NO_PERMISSION_TO_TABLE"

    url = reverse(
        "api:database:rows:move", kwargs={"table_id": table.id, "row_id": 99999}
    )
    response = api_client.patch(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ROW_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:move", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        f"{url}?before_id=-1",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ROW_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:move", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json_row_1 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_1["id"] == row_1.id
    assert response_json_row_1["order"] == "4.00000000000000000000"

    row_1.refresh_from_db()
    row_2.refresh_from_db()
    row_3.refresh_from_db()
    assert row_1.order == Decimal("4.00000000000000000000")
    assert row_2.order == Decimal("2.00000000000000000000")
    assert row_3.order == Decimal("3.00000000000000000000")

    url = reverse(
        "api:database:rows:move", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        f"{url}?before_id={row_3.id}",
        format="json",
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )
    response_json_row_1 = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json_row_1["id"] == row_1.id
    assert response_json_row_1["order"] == "2.50000000000000000000"

    row_1.refresh_from_db()
    row_2.refresh_from_db()
    row_3.refresh_from_db()
    assert row_1.order == Decimal("2.50000000000000000000")
    assert row_2.order == Decimal("2.00000000000000000000")
    assert row_3.order == Decimal("3.00000000000000000000")

    data_fixture.create_text_field(user=user, table=table, name="New Field")
    url = reverse(
        "api:database:rows:move", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.patch(
        f"{url}?user_field_names=true",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json_row_1 = response.json()
    assert response_json_row_1 == {
        "New Field": None,
        "id": row_1.id,
        "order": "4.00000000000000000000",
    }

    # Make sure that we receive an error message when calling move row
    # with an before_id != int
    url = reverse("api:database:rows:move", kwargs={"table_id": table.id, "row_id": 1})
    response = api_client.patch(
        f"{url}?before_id=wrong_type",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert response_json["detail"]["before_id"][0]["code"] == "invalid"
    assert (
        response_json["detail"]["before_id"][0]["error"]
        == "A valid integer is required."
    )


@pytest.mark.django_db
def test_delete_row_by_id(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    data_fixture.create_text_field(
        table=table, order=0, name="Color", text_default="white"
    )
    data_fixture.create_number_field(table=table, order=1, name="Horsepower")
    data_fixture.create_boolean_field(table=table, order=2, name="For sale")

    token = TokenHandler().create_token(user, table.database.workspace, "Good")
    wrong_token = TokenHandler().create_token(user, table.database.workspace, "Wrong")
    TokenHandler().update_token_permissions(user, wrong_token, True, True, True, False)

    model = table.get_model()
    row_1 = model.objects.create()
    row_2 = model.objects.create()
    row_3 = model.objects.create()

    url = reverse("api:database:rows:item", kwargs={"table_id": 9999, "row_id": 9999})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {jwt_token}")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": 9999}
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {jwt_token}")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ROW_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"Token abc123")
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_TOKEN_DOES_NOT_EXIST"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"Token {wrong_token.key}")
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_NO_PERMISSION_TO_TABLE"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table_2.id, "row_id": row_1.id}
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {jwt_token}")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {jwt_token}")
    assert response.status_code == 204

    assert model.objects.count() == 2
    assert model.objects.all()[0].id == row_2.id

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_2.id}
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {jwt_token}")
    assert response.status_code == 204
    assert model.objects.count() == 1

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_3.id}
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"Token {token.key}")
    assert response.status_code == 204
    assert model.objects.count() == 0


@pytest.mark.django_db
def test_list_rows_with_attribute_names(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    table_to_link_with = data_fixture.create_database_table(
        user=user, database=table.database
    )
    data_fixture.create_text_field(
        primary=True,
        name="Primary",
        table=table_to_link_with,
    )
    field_1 = data_fixture.create_text_field(name="Name", table=table, primary=True)
    field_2 = data_fixture.create_number_field(name="Price,", table=table)
    field_3 = data_fixture.create_boolean_field(name='"Name, 2"', table=table)
    link_field = FieldHandler().create_field(
        user, table, "link_row", link_row_table=table_to_link_with, name="Link"
    )

    model = table.get_model()
    row_1 = model.objects.create(
        **{
            f"field_{field_1.id}": "name 1",
            f"field_{field_2.id}": 2,
            f"field_{field_3.id}": False,
        }
    )
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?user_field_names=true",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["results"] == [
        {
            '"Name, 2"': False,
            "Name": "name 1",
            "Price,": "2",
            "id": 1,
            "order": "1.00000000000000000000",
            "Link": [],
        }
    ]

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row_1.id}
    )
    response = api_client.get(
        f"{url}?user_field_names=true",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "id": 1,
        "Name": "name 1",
        '"Name, 2"': False,
        "order": "1.00000000000000000000",
        "Price,": "2",
        "Link": [],
    }

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f'{url}?user_field_names=true&include="\\"Name, 2\\""',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["results"] == [
        {
            '"Name, 2"': False,
            "id": 1,
            "order": "1.00000000000000000000",
        }
    ]

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f'{url}?user_field_names=true&exclude="\\"Name, 2\\""',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["results"] == [
        {
            "Name": "name 1",
            "Price,": "2",
            "id": 1,
            "order": "1.00000000000000000000",
            "Link": [],
        }
    ]

    model.objects.create(
        **{
            f"field_{field_1.id}": "name 2",
            f"field_{field_2.id}": 1,
            f"field_{field_3.id}": True,
        }
    )

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?user_field_names=true&order_by={link_field.name}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert (
        response_json["detail"]
        == "It is not possible to order by Link because the field type "
        "link_row does not support filtering."
    )

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?user_field_names=true&order_by=Name",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["results"] == [
        {
            '"Name, 2"': False,
            "Name": "name 1",
            "Price,": "2",
            "id": 1,
            "order": "1.00000000000000000000",
            "Link": [],
        },
        {
            '"Name, 2"': True,
            "Name": "name 2",
            "Price,": "1",
            "id": 2,
            "order": "1.00000000000000000000",
            "Link": [],
        },
    ]

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f'{url}?user_field_names=true&order_by="-\\"Name, 2\\""',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["results"] == [
        {
            '"Name, 2"': True,
            "Name": "name 2",
            "Price,": "1",
            "id": 2,
            "order": "1.00000000000000000000",
            "Link": [],
        },
        {
            '"Name, 2"': False,
            "Name": "name 1",
            "Price,": "2",
            "id": 1,
            "order": "1.00000000000000000000",
            "Link": [],
        },
    ]

    # make sure that when user_field_names is not set
    # that a correct error is presented when still using
    # a field names in order_by
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?order_by={field_1.name}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_ORDER_BY_FIELD_NOT_FOUND"
    assert (
        response_json["detail"]
        == f"The field {field_1.name} was not found in the table."
    )

    # make sure that when user_field_names is false and we provide
    # a field_id string that we get a result.
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?user_field_names=false&order_by=field_{field_1.id}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["results"] == [
        {
            "id": 1,
            "order": "1.00000000000000000000",
            f"field_{field_1.id}": "name 1",
            f"field_{field_3.id}": False,
            f"field_{field_2.id}": "2",
            f"field_{link_field.id}": [],
        },
        {
            "id": 2,
            "order": "1.00000000000000000000",
            f"field_{field_1.id}": "name 2",
            f"field_{field_3.id}": True,
            f"field_{field_2.id}": "1",
            f"field_{link_field.id}": [],
        },
    ]

    # make sure that when user_field_names is true and we provide
    # a field_id string that we get an error.
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        f"{url}?user_field_names=true&order_by=field_{field_1.id}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_ORDER_BY_FIELD_NOT_FOUND"
    assert (
        response_json["detail"]
        == f"The field field_{field_1.id} was not found in the table."
    )


@pytest.mark.django_db
def test_list_rows_returns_https_next_url(api_client, data_fixture, settings):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    field_1 = data_fixture.create_text_field(name="Name", table=table, primary=True)

    model = table.get_model()
    model.objects.create(
        **{
            f"field_{field_1.id}": "name 1",
        }
    )
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["next"] is None

    for i in range(settings.ROW_PAGE_SIZE_LIMIT + 1):
        model.objects.create(
            **{
                f"field_{field_1.id}": f"name {i}",
            }
        )

    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert (
        response_json["next"] == "http://testserver/api/database/rows/table/"
        f"{table.id}/?page=2"
    )

    settings.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
        HTTP_X_FORWARDED_PROTO="https",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert (
        response_json["next"] == "https://testserver:80/api/database/rows/table/"
        f"{table.id}/?page=2"
    )


@pytest.mark.django_db
def test_list_row_names(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(name="Name", table=table, primary=True)

    # A table for another user
    table_off = data_fixture.create_database_table()

    # A table in the same database
    table_2 = data_fixture.create_database_table(user=user, database=table.database)
    data_fixture.create_text_field(name="Name", table=table_2, primary=True)

    # A table in another database
    table_3 = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(name="Name", table=table_3, primary=True)

    token = TokenHandler().create_token(user, table.database.workspace, "Good")
    wrong_token = TokenHandler().create_token(user, table.database.workspace, "Wrong")
    TokenHandler().update_token_permissions(user, wrong_token, True, False, True, True)

    model = table.get_model(attribute_names=True)
    model.objects.create(name="Alpha")
    model.objects.create(name="Beta")
    model.objects.create(name="Gamma")
    model.objects.create(name="Omega")

    model_2 = table_2.get_model(attribute_names=True)
    model_2.objects.create(name="Monday")
    model_2.objects.create(name="Tuesday")

    model_3 = table_3.get_model(attribute_names=True)
    model_3.objects.create(name="January")

    url = reverse("api:database:rows:names")
    response = api_client.get(
        f"{url}?table__99999=1,2,3",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    response = api_client.get(
        f"{url}?table__{table.id}=1,2,3&table__99999=1,2,3",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    response = api_client.get(
        f"{url}?table__{table_off.id}=1,2,3",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        f"{url}?table__{table.id}=1,2,3",
        format="json",
        HTTP_AUTHORIZATION="Token abc123",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_TOKEN_DOES_NOT_EXIST"

    response = api_client.get(
        f"{url}?table__{table.id}=1,2,3",
        format="json",
        HTTP_AUTHORIZATION=f"Token {wrong_token.key}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_NO_PERMISSION_TO_TABLE"

    user.is_active = False
    user.save()
    response = api_client.get(
        f"{url}?table__{table.id}=1,2,3",
        format="json",
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_USER_NOT_ACTIVE"
    user.is_active = True
    user.save()

    response = api_client.get(
        f"{url}?tabble__{table.id}=1,2,3",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response.json()["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert (
        response.json()["detail"]
        == 'Only table Id prefixed by "table__" are allowed as parameter.'
    )

    response = api_client.get(
        f"{url}?table__12i=1,2,3",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response.json()["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert response.json()["detail"] == 'Failed to parse table id in "table__12i".'

    response = api_client.get(
        f"{url}?table__23=1p,2,3",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response.json()["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert (
        response.json()["detail"]
        == 'Failed to parse row ids in "1p,2,3" for "table__23" parameter.'
    )

    response = api_client.get(
        f"{url}?table__{table.id}=1",
        format="json",
        HTTP_AUTHORIZATION=f"Token {token.key}",
    )
    assert response.status_code == HTTP_200_OK

    # One query one table
    response = api_client.get(
        f"{url}?table__{table.id}=1,2,3",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert response_json == {str(table.id): {"1": "Alpha", "2": "Beta", "3": "Gamma"}}

    # 2 tables, one database
    response = api_client.get(
        f"{url}?table__{table.id}=1,2,3&table__{table_2.id}=1,2",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert response_json == {
        str(table.id): {"1": "Alpha", "2": "Beta", "3": "Gamma"},
        str(table_2.id): {"1": "Monday", "2": "Tuesday"},
    }

    # Two tables, two databases
    response = api_client.get(
        f"{url}?table__{table.id}=1,2,3&table__{table_3.id}=1",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_get_row_adjacent(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    table = data_fixture.create_database_table(name="table", user=user)
    field = data_fixture.create_text_field(name="some name", table=table)

    [row_1, row_2, row_3] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{field.id}": "some value"},
            {f"field_{field.id}": "some value"},
            {f"field_{field.id}": "some value"},
        ],
    )

    # Get the next row
    response = api_client.get(
        reverse(
            "api:database:rows:adjacent",
            kwargs={"table_id": table.id, "row_id": row_2.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
        data={"user_field_names": True},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == row_3.id
    assert field.name in response_json

    # Get the previous row
    response = api_client.get(
        reverse(
            "api:database:rows:adjacent",
            kwargs={"table_id": table.id, "row_id": row_2.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
        data={"previous": True},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == row_1.id


@pytest.mark.django_db
def test_get_row_adjacent_view_id_provided(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    table = data_fixture.create_database_table(name="table", user=user)
    view = data_fixture.create_grid_view(name="view", user=user, table=table)
    field = data_fixture.create_text_field(name="field", table=table)

    data_fixture.create_view_sort(user, field=field, view=view)
    data_fixture.create_view_filter(
        user, field=field, view=view, type="contains", value="a"
    )

    [row_1, row_2, row_3] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{field.id}": "ab"},
            {f"field_{field.id}": "b"},
            {f"field_{field.id}": "a"},
        ],
    )

    response = api_client.get(
        reverse(
            "api:database:rows:adjacent",
            kwargs={"table_id": table.id, "row_id": row_3.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
        data={"view_id": view.id},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == row_1.id


@pytest.mark.django_db
def test_get_row_adjacent_view_id_no_adjacent_row(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    table = data_fixture.create_database_table(name="table", user=user)
    field = data_fixture.create_text_field(name="field", table=table)

    [row_1, row_2, row_3] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{field.id}": "a"},
            {f"field_{field.id}": "b"},
            {f"field_{field.id}": "c"},
        ],
    )

    response = api_client.get(
        reverse(
            "api:database:rows:adjacent",
            kwargs={"table_id": table.id, "row_id": row_3.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_get_row_adjacent_view_invalid_requests(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    user_2, jwt_token_2 = data_fixture.create_user_and_token(
        email="test2@test.nl", password="password", first_name="Test2"
    )
    table = data_fixture.create_database_table(name="table", user=user)
    table_unrelated = data_fixture.create_database_table(
        name="table unrelated", user=user
    )
    view_unrelated = data_fixture.create_grid_view(table=table_unrelated)

    row = RowHandler().create_row(user, table, {})

    response = api_client.get(
        reverse(
            "api:database:rows:adjacent",
            kwargs={"table_id": table.id, "row_id": row.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token_2}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        reverse(
            "api:database:rows:adjacent",
            kwargs={"table_id": 999999, "row_id": row.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.data["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    response = api_client.get(
        reverse(
            "api:database:rows:adjacent",
            kwargs={"table_id": table.id, "row_id": row.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
        data={"view_id": 999999},
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.data["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    response = api_client.get(
        reverse(
            "api:database:rows:adjacent",
            kwargs={"table_id": table.id, "row_id": 99999},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.data["error"] == "ERROR_ROW_DOES_NOT_EXIST"

    response = api_client.get(
        reverse(
            "api:database:rows:adjacent",
            kwargs={"table_id": table.id, "row_id": row.id},
        ),
        format="json",
        data={"view_id": view_unrelated.id},
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.data["error"] == "ERROR_VIEW_DOES_NOT_EXIST"


@pytest.mark.django_db
@pytest.mark.parametrize("search_mode", ALL_SEARCH_MODES)
def test_get_row_adjacent_search(api_client, data_fixture, search_mode):
    user, jwt_token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    table = data_fixture.create_database_table(name="table", user=user)
    field = data_fixture.create_text_field(name="field", table=table)

    [row_1, row_2, row_3] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{field.id}": "a"},
            {f"field_{field.id}": "ab"},
            {f"field_{field.id}": "c"},
        ],
    )
    SearchHandler.update_tsvector_columns(
        table, update_tsvectors_for_changed_rows_only=False
    )

    response = api_client.get(
        reverse(
            "api:database:rows:adjacent",
            kwargs={"table_id": table.id, "row_id": row_2.id},
        ),
        data={"search": "a", "search_mode": search_mode},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT, response.json()


@pytest.mark.django_db
@pytest.mark.row_history
def test_list_row_history_for_different_rows(data_fixture, api_client):
    user, jwt_token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(
        name="Test", user=user, database=database
    )
    name_field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )
    number_field = data_fixture.create_number_field(
        table=table, name="Number", number_decimal_places=2
    )

    row_handler = RowHandler()

    row_one = row_handler.create_row(user, table, {name_field.id: "Original 1"})
    row_two = row_handler.create_row(user, table, {name_field.id: "Original 2"})

    with freeze_time("2021-01-01 12:00"):
        action_type_registry.get_by_type(UpdateRowsActionType).do(
            user,
            table,
            [
                {
                    "id": row_one.id,
                    f"field_{name_field.id}": "New 1",
                    f"field_{number_field.id}": "1.00",
                },
                {
                    "id": row_two.id,
                    f"field_{name_field.id}": "New 2",
                    f"field_{number_field.id}": None,
                },
            ],
        )

    with freeze_time("2021-01-01 12:01"):
        action_type_registry.get_by_type(UpdateRowsActionType).do(
            user,
            table,
            [{"id": row_one.id, f"field_{name_field.id}": "New 1.1"}],
        )

    response = api_client.get(
        reverse(
            "api:database:rows:history",
            kwargs={"table_id": table.id, "row_id": row_one.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2021-01-01T12:01:00Z",
                "before": {
                    f"field_{name_field.id}": "New 1",
                },
                "after": {
                    f"field_{name_field.id}": "New 1.1",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    }
                },
            },
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2021-01-01T12:00:00Z",
                "before": {
                    f"field_{name_field.id}": "Original 1",
                    f"field_{number_field.id}": None,
                },
                "after": {
                    f"field_{name_field.id}": "New 1",
                    f"field_{number_field.id}": "1.00",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    },
                    f"field_{number_field.id}": {
                        "id": number_field.id,
                        "type": "number",
                        "number_decimal_places": 2,
                        "number_negative": False,
                    },
                },
            },
        ],
    }

    response = api_client.get(
        reverse(
            "api:database:rows:history",
            kwargs={"table_id": table.id, "row_id": row_two.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2021-01-01T12:00:00Z",
                "before": {
                    f"field_{name_field.id}": "Original 2",
                },
                "after": {
                    f"field_{name_field.id}": "New 2",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    }
                },
            },
        ],
    }


@pytest.mark.django_db
@pytest.mark.row_history
def test_list_row_history_for_different_fields(data_fixture, api_client):
    workspace = data_fixture.create_workspace()
    user2 = data_fixture.create_user(workspace=workspace)
    user3 = data_fixture.create_user(workspace=workspace)
    user, jwt_token = data_fixture.create_user_and_token(workspace=workspace)
    database = data_fixture.create_database_application(user=user, workspace=workspace)
    table = data_fixture.create_database_table(
        name="Test", user=user, database=database
    )
    table2 = data_fixture.create_database_table(user=user, database=table.database)
    name_field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )
    number_field = data_fixture.create_number_field(
        table=table, name="Number", number_decimal_places=2
    )
    email_field = data_fixture.create_email_field(table=table, name="Email")
    url_field = data_fixture.create_url_field(table=table, name="URL")
    rating_field = data_fixture.create_rating_field(
        table=table, user=user, name="Rating", max_value=5
    )
    boolean_field = data_fixture.create_boolean_field(table=table, name="Boolean")
    phone_field = data_fixture.create_phone_number_field(table=table, name="Phone")
    date_field = data_fixture.create_date_field(
        table=table, date_include_time=False, date_format="ISO", name="Date"
    )
    datetime_field = data_fixture.create_date_field(
        table=table, date_include_time=True, date_format="ISO", name="Date"
    )
    file_field = data_fixture.create_file_field(table=table, name="File")
    file1 = data_fixture.create_user_file(
        original_name="test.txt",
        is_image=True,
    )
    file1.uploaded_at = datetime(2021, 1, 1, 12, 30, tzinfo=timezone.utc)
    file1.save()
    file2 = data_fixture.create_user_file(
        original_name="test2.txt",
        is_image=True,
    )
    single_select_field = data_fixture.create_single_select_field(
        table=table, name="Single select"
    )
    option_a = data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    option_b = data_fixture.create_select_option(
        field=single_select_field, value="B", color="red"
    )
    multiple_select_field = data_fixture.create_multiple_select_field(
        table=table, name="Multiple select"
    )
    multi_option_a = data_fixture.create_select_option(
        field=multiple_select_field, value="A", color="blue"
    )
    multi_option_b = data_fixture.create_select_option(
        field=multiple_select_field, value="B", color="red"
    )
    multiple_select_field.select_options.set([multi_option_a, multi_option_b])
    collaborator_field = data_fixture.create_multiple_collaborators_field(
        table=table, name="Collaborators", notify_user_when_added=False
    )
    linkrow_field = FieldHandler().create_field(
        user,
        table,
        "link_row",
        name="linkrowfield",
        link_row_table=table2,
    )
    table2_model = table2.get_model()
    table2_row1 = table2_model.objects.create()
    table2_row2 = table2_model.objects.create()

    row_handler = RowHandler()

    row_one = row_handler.create_row(
        user,
        table,
        {
            name_field.id: "Original 1",
            number_field.id: "0.00",
            email_field.id: "test@example.com",
            url_field.id: "http://baserow.io",
            rating_field.id: 3,
            boolean_field.id: False,
            phone_field.id: "123456789",
            date_field.id: "2023-06-06",
            datetime_field.id: "2023-06-06T12:00",
            file_field.id: [{"name": file1.name, "visible_name": "file 1"}],
            single_select_field.id: option_a,
            multiple_select_field.id: [multi_option_a.id],
            collaborator_field.id: [{"id": user2.id}, {"id": user3.id}],
            linkrow_field.id: [table2_row1.id],
        },
    )

    with freeze_time("2021-01-01 12:00"):
        action_type_registry.get_by_type(UpdateRowsActionType).do(
            user,
            table,
            [
                {
                    "id": row_one.id,
                    f"field_{name_field.id}": "New 1",
                    f"field_{number_field.id}": "1.00",
                    f"field_{email_field.id}": "test2@example.com",
                    f"field_{url_field.id}": "https://baserow.io",
                    f"field_{rating_field.id}": 5,
                    f"field_{boolean_field.id}": True,
                    f"field_{phone_field.id}": "123456790",
                    f"field_{date_field.id}": "2023-06-07",
                    f"field_{datetime_field.id}": "2023-06-06T13:00",
                    f"field_{file_field.id}": [
                        {"name": file1.name, "visible_name": "file 1"},
                        {"name": file2.name, "visible_name": "file 2"},
                    ],
                    f"field_{single_select_field.id}": option_b.id,
                    f"field_{multiple_select_field.id}": [
                        multi_option_a.id,
                        multi_option_b.id,
                    ],
                    f"field_{collaborator_field.id}": [{"id": user2.id}],
                    f"field_{linkrow_field.id}": [table2_row1.id, table2_row2.id],
                },
            ],
        )

    response = api_client.get(
        reverse(
            "api:database:rows:history",
            kwargs={"table_id": table.id, "row_id": row_one.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2021-01-01T12:00:00Z",
                "before": {
                    f"field_{name_field.id}": "Original 1",
                    f"field_{number_field.id}": "0.00",
                    f"field_{email_field.id}": "test@example.com",
                    f"field_{url_field.id}": "http://baserow.io",
                    f"field_{rating_field.id}": 3,
                    f"field_{boolean_field.id}": False,
                    f"field_{phone_field.id}": "123456789",
                    f"field_{date_field.id}": "2023-06-06",
                    f"field_{datetime_field.id}": "2023-06-06 12:00:00+00:00",
                    f"field_{file_field.id}": [
                        {
                            "name": file1.name,
                            "visible_name": "file 1",
                            "image_height": None,
                            "image_width": None,
                            "is_image": True,
                            "mime_type": "text/plain",
                            "size": 100,
                            "uploaded_at": "2021-01-01T12:30:00+00:00",
                        },
                    ],
                    f"field_{single_select_field.id}": option_a.id,
                    f"field_{multiple_select_field.id}": [multi_option_a.id],
                    f"field_{collaborator_field.id}": [
                        {"id": user2.id},
                        {"id": user3.id},
                    ],
                    f"field_{linkrow_field.id}": [table2_row1.id],
                },
                "after": {
                    f"field_{name_field.id}": "New 1",
                    f"field_{number_field.id}": "1.00",
                    f"field_{email_field.id}": "test2@example.com",
                    f"field_{url_field.id}": "https://baserow.io",
                    f"field_{rating_field.id}": 5,
                    f"field_{boolean_field.id}": True,
                    f"field_{phone_field.id}": "123456790",
                    f"field_{date_field.id}": "2023-06-07",
                    f"field_{datetime_field.id}": "2023-06-06T13:00",
                    f"field_{file_field.id}": [
                        {"name": file1.name, "visible_name": "file 1"},
                        {"name": file2.name, "visible_name": "file 2"},
                    ],
                    f"field_{single_select_field.id}": option_b.id,
                    f"field_{multiple_select_field.id}": [
                        multi_option_a.id,
                        multi_option_b.id,
                    ],
                    f"field_{collaborator_field.id}": [
                        {"id": user2.id},
                    ],
                    f"field_{linkrow_field.id}": [table2_row1.id, table2_row2.id],
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    },
                    f"field_{number_field.id}": {
                        "id": number_field.id,
                        "number_decimal_places": 2,
                        "number_negative": False,
                        "type": "number",
                    },
                    f"field_{email_field.id}": {
                        "id": email_field.id,
                        "type": "email",
                    },
                    f"field_{url_field.id}": {
                        "id": url_field.id,
                        "type": "url",
                    },
                    f"field_{rating_field.id}": {
                        "id": rating_field.id,
                        "type": "rating",
                    },
                    f"field_{boolean_field.id}": {
                        "id": boolean_field.id,
                        "type": "boolean",
                    },
                    f"field_{phone_field.id}": {
                        "id": phone_field.id,
                        "type": "phone_number",
                    },
                    f"field_{date_field.id}": {
                        "id": date_field.id,
                        "type": "date",
                        "date_force_timezone": None,
                        "date_format": "ISO",
                        "date_include_time": False,
                        "date_time_format": "24",
                        "date_show_tzinfo": False,
                    },
                    f"field_{datetime_field.id}": {
                        "id": datetime_field.id,
                        "type": "date",
                        "date_force_timezone": None,
                        "date_format": "ISO",
                        "date_include_time": True,
                        "date_time_format": "24",
                        "date_show_tzinfo": False,
                    },
                    f"field_{file_field.id}": {
                        "id": file_field.id,
                        "type": "file",
                    },
                    f"field_{single_select_field.id}": {
                        "id": single_select_field.id,
                        "select_options": {
                            f"{option_a.id}": {
                                "color": option_a.color,
                                "id": option_a.id,
                                "value": option_a.value,
                            },
                            f"{option_b.id}": {
                                "color": option_b.color,
                                "id": option_b.id,
                                "value": option_b.value,
                            },
                        },
                        "type": "single_select",
                    },
                    f"field_{multiple_select_field.id}": {
                        "id": multiple_select_field.id,
                        "select_options": {
                            f"{multi_option_a.id}": {
                                "color": multi_option_a.color,
                                "id": multi_option_a.id,
                                "value": multi_option_a.value,
                            },
                            f"{multi_option_b.id}": {
                                "color": multi_option_b.color,
                                "id": multi_option_b.id,
                                "value": multi_option_b.value,
                            },
                        },
                        "type": "multiple_select",
                    },
                    f"field_{collaborator_field.id}": {
                        "id": collaborator_field.id,
                        "type": "multiple_collaborators",
                        "collaborators": {
                            f"{user2.id}": {"id": user2.id, "name": user2.first_name},
                            f"{user3.id}": {"id": user3.id, "name": user3.first_name},
                        },
                    },
                    f"field_{linkrow_field.id}": {
                        "id": linkrow_field.id,
                        "type": "link_row",
                        "linked_rows": {
                            f"{table2_row1.id}": {
                                "value": f"unnamed row {table2_row1.id}"
                            },
                            f"{table2_row2.id}": {
                                "value": f"unnamed row {table2_row2.id}"
                            },
                        },
                    },
                },
            },
        ],
    }


@pytest.mark.django_db
@pytest.mark.row_history
def test_undo_redo_create_new_entries_in_row_history(data_fixture, api_client):
    session_id = "session_id"
    user, jwt_token = data_fixture.create_user_and_token(session_id=session_id)
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(
        name="Test", user=user, database=database
    )
    name_field = data_fixture.create_text_field(table=table, name="Name")

    row_handler = RowHandler()

    row = row_handler.create_row(user, table, {name_field.id: "Original 1"})

    with freeze_time("2021-01-01 12:00"):
        action_type_registry.get_by_type(UpdateRowsActionType).do(
            user,
            table,
            [
                {"id": row.id, f"field_{name_field.id}": "New 1"},
            ],
        )

    # undo
    with freeze_time("2021-01-01 12:01"):
        actions = ActionHandler.undo(
            user, [UpdateRowsActionType.scope(table.id)], session_id
        )
        assert_undo_redo_actions_are_valid(actions, [UpdateRowsActionType])

    response = api_client.get(
        reverse(
            "api:database:rows:history",
            kwargs={"table_id": table.id, "row_id": row.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2021-01-01T12:01:00Z",
                "before": {
                    f"field_{name_field.id}": "New 1",
                },
                "after": {
                    f"field_{name_field.id}": "Original 1",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    },
                },
            },
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2021-01-01T12:00:00Z",
                "before": {
                    f"field_{name_field.id}": "Original 1",
                },
                "after": {
                    f"field_{name_field.id}": "New 1",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    },
                },
            },
        ],
    }

    # redo
    with freeze_time("2021-01-01 12:02"):
        actions = ActionHandler.redo(
            user, [UpdateRowsActionType.scope(table.id)], session_id
        )
        assert_undo_redo_actions_are_valid(actions, [UpdateRowsActionType])

    response = api_client.get(
        reverse(
            "api:database:rows:history",
            kwargs={"table_id": table.id, "row_id": row.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 3,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2021-01-01T12:02:00Z",
                "before": {
                    f"field_{name_field.id}": "Original 1",
                },
                "after": {
                    f"field_{name_field.id}": "New 1",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    },
                },
            },
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2021-01-01T12:01:00Z",
                "before": {
                    f"field_{name_field.id}": "New 1",
                },
                "after": {
                    f"field_{name_field.id}": "Original 1",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    },
                },
            },
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2021-01-01T12:00:00Z",
                "before": {
                    f"field_{name_field.id}": "Original 1",
                },
                "after": {
                    f"field_{name_field.id}": "New 1",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    },
                },
            },
        ],
    }


@pytest.mark.django_db
@pytest.mark.row_history
def test_list_row_history_endpoint_handle_errors_correctly(data_fixture, api_client):
    user, jwt_token = data_fixture.create_user_and_token()
    _, other_token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(
        name="Test", user=user, database=database
    )
    name_field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )
    row = RowHandler().create_row(user, table, {name_field.id: "Original 1"})

    with freeze_time("2021-01-01 12:01"):
        action_type_registry.get_by_type(UpdateRowsActionType).do(
            user,
            table,
            [{"id": row.id, f"field_{name_field.id}": "New 1.1"}],
        )

    response = api_client.get(
        reverse(
            "api:database:rows:history",
            kwargs={"table_id": table.id, "row_id": row.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {other_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        reverse(
            "api:database:rows:history",
            kwargs={"table_id": 9999, "row_id": row.id},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"

    response = api_client.get(
        reverse(
            "api:database:rows:history",
            kwargs={"table_id": table.id, "row_id": 9999},
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ROW_DOES_NOT_EXIST"


@pytest.mark.django_db
@pytest.mark.row_history
@override_settings(ROW_PAGE_SIZE_LIMIT=10)
def test_list_row_history_endpoint_is_paginated(data_fixture, api_client):
    user, jwt_token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(
        name="Test", user=user, database=database
    )
    name_field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )
    row = RowHandler().create_row(user, table, {name_field.id: "Original 1"})

    for i in range(5):
        timestamp = datetime(2023, 1, 1, 12) + timedelta(minutes=i)
        with freeze_time(timestamp):
            action_type_registry.get_by_type(UpdateRowsActionType).do(
                user,
                table,
                [{"id": row.id, f"field_{name_field.id}": f"New 1.{i}"}],
            )

    response = api_client.get(
        reverse(
            "api:database:rows:history",
            kwargs={"table_id": table.id, "row_id": row.id},
        )
        + "?limit=2",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 5,
        "next": f"http://testserver/api/database/rows/table/{table.id}/{row.id}/history/?limit=2&offset=2",
        "previous": None,
        "results": [
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2023-01-01T12:04:00Z",
                "before": {
                    f"field_{name_field.id}": "New 1.3",
                },
                "after": {
                    f"field_{name_field.id}": "New 1.4",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    }
                },
            },
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2023-01-01T12:03:00Z",
                "before": {
                    f"field_{name_field.id}": "New 1.2",
                },
                "after": {
                    f"field_{name_field.id}": "New 1.3",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    }
                },
            },
        ],
    }

    # Use offset
    response = api_client.get(
        reverse(
            "api:database:rows:history",
            kwargs={"table_id": table.id, "row_id": row.id},
        )
        + "?offset=3",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 5,
        "next": None,
        "previous": f"http://testserver/api/database/rows/table/{table.id}/{row.id}/history/?limit=10",
        "results": [
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2023-01-01T12:01:00Z",
                "before": {
                    f"field_{name_field.id}": "New 1.0",
                },
                "after": {
                    f"field_{name_field.id}": "New 1.1",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    }
                },
            },
            {
                "id": AnyInt(),
                "action_type": "update_rows",
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                },
                "timestamp": "2023-01-01T12:00:00Z",
                "before": {
                    f"field_{name_field.id}": "Original 1",
                },
                "after": {
                    f"field_{name_field.id}": "New 1.0",
                },
                "fields_metadata": {
                    f"field_{name_field.id}": {
                        "id": name_field.id,
                        "type": "text",
                    }
                },
            },
        ],
    }

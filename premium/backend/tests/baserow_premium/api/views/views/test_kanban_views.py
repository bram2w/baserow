import pytest
from unittest.mock import patch
from django.shortcuts import reverse
from django.test.utils import override_settings
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_402_PAYMENT_REQUIRED,
    HTTP_404_NOT_FOUND,
)

from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.action.scopes import ViewActionScopeType
from baserow.contrib.database.views.actions import UpdateViewActionType
from baserow.contrib.database.views.models import View
from baserow.contrib.database.views.handler import ViewHandler
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid

from baserow_premium.views.models import KanbanView


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_list_without_valid_premium_license(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=False
    )
    kanban = premium_data_fixture.create_kanban_view(user=user)
    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_402_PAYMENT_REQUIRED
    assert response.json()["error"] == "ERROR_NO_ACTIVE_PREMIUM_LICENSE"

    # The kanban view should work if it's a template.
    premium_data_fixture.create_template(group=kanban.table.database.group)
    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_list_without_valid_premium_license_for_group(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    kanban = premium_data_fixture.create_kanban_view(user=user)

    with patch(
        "baserow_premium.license.handler.has_active_premium_license_for"
    ) as mock_has_active_premium_license_for:
        mock_has_active_premium_license_for.return_value = [{"type": "group", "id": 0}]
        url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
        response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
        assert response.status_code == HTTP_402_PAYMENT_REQUIRED
        assert response.json()["error"] == "ERROR_NO_ACTIVE_PREMIUM_LICENSE"

    with patch(
        "baserow_premium.license.handler.has_active_premium_license_for"
    ) as mock_has_active_premium_license_for:
        mock_has_active_premium_license_for.return_value = [
            {"type": "group", "id": kanban.table.database.group.id}
        ]
        premium_data_fixture.create_template(group=kanban.table.database.group)
        url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
        response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
        assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_list_rows_invalid_parameters(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        has_active_premium_license=True,
    )
    kanban = premium_data_fixture.create_kanban_view(
        user=user, single_select_field=None
    )
    kanban_2 = premium_data_fixture.create_kanban_view()

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": 0})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_KANBAN_DOES_NOT_EXIST"

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban_2.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_list_rows_include_field_options(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        has_active_premium_license=True,
    )
    table = premium_data_fixture.create_database_table(user=user)
    text_field = premium_data_fixture.create_text_field(table=table, primary=True)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    kanban = premium_data_fixture.create_kanban_view(
        table=table, single_select_field=single_select_field
    )

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?include=field_options", **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert len(response_json["field_options"]) == 2
    assert response_json["field_options"][str(text_field.id)]["hidden"] is True
    assert response_json["field_options"][str(text_field.id)]["order"] == 32767
    assert response_json["field_options"][str(single_select_field.id)]["hidden"] is True
    assert response_json["field_options"][str(single_select_field.id)]["order"] == 32767


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_list_all_rows(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    text_field = premium_data_fixture.create_text_field(table=table, primary=True)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    option_b = premium_data_fixture.create_select_option(
        field=single_select_field, value="B", color="red"
    )
    kanban = premium_data_fixture.create_kanban_view(
        table=table, single_select_field=single_select_field
    )

    model = table.get_model()
    row_none = model.objects.create(
        **{
            f"field_{text_field.id}": "Row None",
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_a1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row A1",
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_a2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row A2",
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_b1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row B1",
            f"field_{single_select_field.id}_id": option_b.id,
        }
    )
    row_b2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row B2",
            f"field_{single_select_field.id}_id": option_b.id,
        }
    )

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["rows"]) == 3

    assert response_json["rows"]["null"]["count"] == 1
    assert len(response_json["rows"]["null"]["results"]) == 1
    assert response_json["rows"]["null"]["results"][0] == {
        "id": row_none.id,
        "order": "1.00000000000000000000",
        f"field_{text_field.id}": "Row None",
        f"field_{single_select_field.id}": None,
    }

    assert response_json["rows"][str(option_a.id)]["count"] == 2
    assert len(response_json["rows"][str(option_a.id)]["results"]) == 2
    assert response_json["rows"][str(option_a.id)]["results"][0] == {
        "id": row_a1.id,
        "order": "1.00000000000000000000",
        f"field_{text_field.id}": "Row A1",
        f"field_{single_select_field.id}": {
            "id": option_a.id,
            "value": "A",
            "color": "blue",
        },
    }
    assert response_json["rows"][str(option_a.id)]["results"][1] == {
        "id": row_a2.id,
        "order": "1.00000000000000000000",
        f"field_{text_field.id}": "Row A2",
        f"field_{single_select_field.id}": {
            "id": option_a.id,
            "value": "A",
            "color": "blue",
        },
    }

    assert response_json["rows"][str(option_b.id)]["count"] == 2
    assert len(response_json["rows"][str(option_b.id)]["results"]) == 2
    assert response_json["rows"][str(option_b.id)]["results"][0] == {
        "id": row_b1.id,
        "order": "1.00000000000000000000",
        f"field_{text_field.id}": "Row B1",
        f"field_{single_select_field.id}": {
            "id": option_b.id,
            "value": "B",
            "color": "red",
        },
    }
    assert response_json["rows"][str(option_b.id)]["results"][1] == {
        "id": row_b2.id,
        "order": "1.00000000000000000000",
        f"field_{text_field.id}": "Row B2",
        f"field_{single_select_field.id}": {
            "id": option_b.id,
            "value": "B",
            "color": "red",
        },
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_list_with_specific_select_options(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    kanban = premium_data_fixture.create_kanban_view(
        table=table, single_select_field=single_select_field
    )

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?select_option={option_a.id}",
        **{"HTTP_AUTHORIZATION": f"JWT" f" {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 1
    assert response_json["rows"][str(option_a.id)]["count"] == 0
    assert len(response_json["rows"][str(option_a.id)]["results"]) == 0

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?select_option=null",
        **{"HTTP_AUTHORIZATION": f"JWT" f" {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 1
    assert response_json["rows"]["null"]["count"] == 0
    assert len(response_json["rows"]["null"]["results"]) == 0

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?select_option={option_a.id}&select_option=null",
        **{"HTTP_AUTHORIZATION": f"JWT" f" {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["rows"]) == 2
    assert response_json["rows"]["null"]["count"] == 0
    assert len(response_json["rows"]["null"]["results"]) == 0
    assert response_json["rows"][str(option_a.id)]["count"] == 0
    assert len(response_json["rows"][str(option_a.id)]["results"]) == 0


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_list_all_rows_with_limit_and_offset(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    kanban = premium_data_fixture.create_kanban_view(
        table=table, single_select_field=single_select_field
    )

    model = table.get_model()
    row_none1 = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_none2 = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_a1 = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_a2 = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?limit=1&offset=1", **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["rows"]) == 2
    assert response_json["rows"]["null"]["count"] == 2
    assert len(response_json["rows"]["null"]["results"]) == 1
    assert response_json["rows"]["null"]["results"][0]["id"] == row_none2.id
    assert response_json["rows"][str(option_a.id)]["count"] == 2
    assert len(response_json["rows"][str(option_a.id)]["results"]) == 1
    assert response_json["rows"][str(option_a.id)]["results"][0]["id"] == row_a2.id

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?select_option=null,1,1", **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 1
    assert response_json["rows"]["null"]["count"] == 2
    assert len(response_json["rows"]["null"]["results"]) == 1
    assert response_json["rows"]["null"]["results"][0]["id"] == row_none2.id

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?select_option={option_a.id},1,1",
        **{"HTTP_AUTHORIZATION": f"JWT" f" {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 1
    assert response_json["rows"][str(option_a.id)]["count"] == 2
    assert len(response_json["rows"][str(option_a.id)]["results"]) == 1
    assert response_json["rows"][str(option_a.id)]["results"][0]["id"] == row_a2.id

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?select_option={option_a.id},1,1&select_option=null,2,0",
        **{"HTTP_AUTHORIZATION": f"JWT" f" {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["rows"]) == 2
    assert response_json["rows"]["null"]["count"] == 2
    assert len(response_json["rows"]["null"]["results"]) == 2
    assert response_json["rows"]["null"]["results"][0]["id"] == row_none1.id
    assert response_json["rows"]["null"]["results"][1]["id"] == row_none2.id
    assert response_json["rows"][str(option_a.id)]["count"] == 2
    assert len(response_json["rows"][str(option_a.id)]["results"]) == 1
    assert response_json["rows"][str(option_a.id)]["results"][0]["id"] == row_a2.id

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?select_option={option_a.id},2,0&select_option=null&limit=1&offset=1",
        **{"HTTP_AUTHORIZATION": f"JWT" f" {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["rows"]) == 2
    assert response_json["rows"]["null"]["count"] == 2
    assert len(response_json["rows"]["null"]["results"]) == 1
    assert response_json["rows"]["null"]["results"][0]["id"] == row_none2.id
    assert response_json["rows"][str(option_a.id)]["count"] == 2
    assert len(response_json["rows"][str(option_a.id)]["results"]) == 2
    assert response_json["rows"][str(option_a.id)]["results"][0]["id"] == row_a1.id
    assert response_json["rows"][str(option_a.id)]["results"][1]["id"] == row_a2.id


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_kanban_filter(api_client, data_fixture, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    number_field = data_fixture.create_number_field(
        table=table, name="FilterNumberField"
    )
    kanban = premium_data_fixture.create_kanban_view(
        table=table, single_select_field=single_select_field
    )
    threshold = 20
    lower_than_threshold = threshold - 1
    higher_than_threshold = threshold + 1
    ViewHandler().create_filter(
        user=user,
        view=kanban,
        type_name="lower_than",
        value=threshold,
        field=number_field,
    )
    model = table.get_model()
    row_null_lower = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": None,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_null_lower2 = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": None,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_null_higher = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": None,
            f"field_{number_field.id}": higher_than_threshold,
        }
    )
    row_a_lower = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_a.id,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_a_lower2 = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_a.id,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_a_higher = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_a.id,
            f"field_{number_field.id}": higher_than_threshold,
        }
    )

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(f"{url}", **{"HTTP_AUTHORIZATION": f"JWT {token}"})

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["rows"]) == 2
    assert response_json["rows"]["null"]["count"] == 2
    assert len(response_json["rows"]["null"]["results"]) == 2
    assert response_json["rows"]["null"]["results"][0]["id"] == row_null_lower.id
    assert response_json["rows"][str(option_a.id)]["count"] == 2
    assert len(response_json["rows"][str(option_a.id)]["results"]) == 2
    assert response_json["rows"][str(option_a.id)]["results"][0]["id"] == row_a_lower.id


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_kanban_filter_limit_offset(api_client, data_fixture, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    number_field = data_fixture.create_number_field(
        table=table, name="FilterNumberField"
    )
    kanban = premium_data_fixture.create_kanban_view(
        table=table, single_select_field=single_select_field
    )
    threshold = 20
    lower_than_threshold = threshold - 1
    higher_than_threshold = threshold + 1
    ViewHandler().create_filter(
        user=user,
        view=kanban,
        type_name="lower_than",
        value=threshold,
        field=number_field,
    )
    model = table.get_model()
    row_null_lower = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": None,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_null_lower2 = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": None,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_null_higher = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": None,
            f"field_{number_field.id}": higher_than_threshold,
        }
    )
    row_a_lower = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_a.id,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_a_lower2 = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_a.id,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_a_higher = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_a.id,
            f"field_{number_field.id}": higher_than_threshold,
        }
    )

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?filter=1&offset=1", **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["rows"]) == 2
    assert response_json["rows"]["null"]["count"] == 2
    assert len(response_json["rows"]["null"]["results"]) == 1
    assert response_json["rows"]["null"]["results"][0]["id"] == row_null_lower2.id
    assert response_json["rows"][str(option_a.id)]["count"] == 2
    assert len(response_json["rows"][str(option_a.id)]["results"]) == 1
    assert (
        response_json["rows"][str(option_a.id)]["results"][0]["id"] == row_a_lower2.id
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_kanban_filter_specific_options_limit_offset(
    api_client, data_fixture, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    option_b = premium_data_fixture.create_select_option(
        field=single_select_field, value="B", color="green"
    )
    number_field = data_fixture.create_number_field(
        table=table, name="FilterNumberField"
    )
    kanban = premium_data_fixture.create_kanban_view(
        table=table, single_select_field=single_select_field
    )
    threshold = 20
    lower_than_threshold = threshold - 1
    higher_than_threshold = threshold + 1
    ViewHandler().create_filter(
        user=user,
        view=kanban,
        type_name="lower_than",
        value=threshold,
        field=number_field,
    )
    model = table.get_model()
    row_null_lower = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": None,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_null_lower2 = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": None,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_null_higher = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": None,
            f"field_{number_field.id}": higher_than_threshold,
        }
    )
    row_a_lower = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_a.id,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_a_lower2 = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_a.id,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )
    row_a_higher = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_a.id,
            f"field_{number_field.id}": higher_than_threshold,
        }
    )
    row_b_lower = model.objects.create(
        **{
            f"field_{single_select_field.id}_id": option_b.id,
            f"field_{number_field.id}": lower_than_threshold,
        }
    )

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?select_option=null,1,1&select_option={option_a.id},2,0",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["rows"]) == 2
    assert response_json["rows"]["null"]["count"] == 2
    assert len(response_json["rows"]["null"]["results"]) == 1
    assert response_json["rows"]["null"]["results"][0]["id"] == row_null_lower2.id
    assert response_json["rows"][str(option_a.id)]["count"] == 2
    assert len(response_json["rows"][str(option_a.id)]["results"]) == 2
    assert response_json["rows"][str(option_a.id)]["results"][0]["id"] == row_a_lower.id


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_list_all_invalid_select_option_parameter(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    kanban = premium_data_fixture.create_kanban_view(
        table=table, single_select_field=single_select_field
    )

    url = reverse("api:database:views:kanban:list", kwargs={"view_id": kanban.id})
    response = api_client.get(
        f"{url}?select_option=null,a",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_INVALID_SELECT_OPTION_PARAMETER"

    response = api_client.get(
        f"{url}?select_option=null,1,1&select_option=1,1,a",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_INVALID_SELECT_OPTION_PARAMETER"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_patch_kanban_view_field_options(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        has_active_premium_license=True,
    )
    table = premium_data_fixture.create_database_table(user=user)
    text_field = premium_data_fixture.create_text_field(table=table)
    kanban = premium_data_fixture.create_kanban_view(
        table=table, single_select_field=None
    )

    url = reverse("api:database:views:field_options", kwargs={"view_id": kanban.id})
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
    options = kanban.get_field_options()
    assert len(options) == 1
    assert options[0].field_id == text_field.id
    assert options[0].hidden is False
    assert options[0].order == 32767


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_kanban_view(api_client, data_fixture, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    single_select_field_2 = premium_data_fixture.create_single_select_field()
    cover_image_file_field = data_fixture.create_file_field(table=table)

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "name": "Test 1",
            "type": "kanban",
            "filter_type": "OR",
            "filters_disabled": True,
            "single_select_field": single_select_field_2.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert (
        response_json["error"]
        == "ERROR_KANBAN_VIEW_FIELD_DOES_NOT_BELONG_TO_SAME_TABLE"
    )

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "name": "Test 1",
            "type": "kanban",
            "filter_type": "OR",
            "filters_disabled": True,
            "single_select_field": None,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Test 1"
    assert response_json["type"] == "kanban"
    assert response_json["filter_type"] == "OR"
    assert response_json["filters_disabled"] is True
    assert response_json["single_select_field"] is None

    kanban_view = KanbanView.objects.all().last()
    assert kanban_view.id == response_json["id"]
    assert kanban_view.single_select_field is None

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "name": "Test 2",
            "type": "kanban",
            "filter_type": "AND",
            "filters_disabled": False,
            "single_select_field": single_select_field.id,
            "card_cover_image_field": cover_image_file_field.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Test 2"
    assert response_json["type"] == "kanban"
    assert response_json["filter_type"] == "AND"
    assert response_json["filters_disabled"] is False
    assert response_json["single_select_field"] == single_select_field.id
    assert response_json["card_cover_image_field"] == cover_image_file_field.id

    kanban_view = KanbanView.objects.all().last()
    assert kanban_view.id == response_json["id"]
    assert kanban_view.single_select_field_id == single_select_field.id


@pytest.mark.django_db
def test_create_kanban_view_invalid_card_cover_image_field(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    text = data_fixture.create_text_field(table=table)
    file_field = data_fixture.create_file_field()

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {"name": "Test 2", "type": "kanban", "card_cover_image_field": text.id},
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
        {"name": "Test 2", "type": "kanban", "card_cover_image_field": file_field.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_FIELD_NOT_IN_TABLE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_update_kanban_view(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    kanban_view = premium_data_fixture.create_kanban_view(
        table=table, single_select_field=None
    )
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    single_select_field_2 = premium_data_fixture.create_single_select_field()

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": kanban_view.id}),
        {
            "single_select_field": single_select_field_2.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert (
        response_json["error"]
        == "ERROR_KANBAN_VIEW_FIELD_DOES_NOT_BELONG_TO_SAME_TABLE"
    )

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": kanban_view.id}),
        {
            "single_select_field": single_select_field.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["single_select_field"] == single_select_field.id

    kanban_view.refresh_from_db()
    assert kanban_view.single_select_field_id == single_select_field.id

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": kanban_view.id}),
        {
            "single_select_field": None,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["single_select_field"] is None

    kanban_view.refresh_from_db()
    assert kanban_view.single_select_field is None


@pytest.mark.django_db
def test_update_kanban_view_card_cover_image_field(
    api_client, data_fixture, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    cover_image_file_field = data_fixture.create_file_field(table=table)
    kanban_view = premium_data_fixture.create_kanban_view(
        table=table, card_cover_image_field=None
    )

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": kanban_view.id}),
        {
            "card_cover_image_field": cover_image_file_field.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["card_cover_image_field"] == cover_image_file_field.id


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_update_kanban_view(data_fixture, premium_data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = premium_data_fixture.create_database_table(user=user)
    single_select_field_1 = premium_data_fixture.create_single_select_field(table=table)
    single_select_field_2 = premium_data_fixture.create_single_select_field(table=table)
    cover_image_file_field_1 = data_fixture.create_file_field(table=table)
    cover_image_file_field_2 = data_fixture.create_file_field(table=table)
    kanban_view = premium_data_fixture.create_kanban_view(table=table)

    original_kanban_data = {
        "name": "Test Original",
        "filter_type": "AND",
        "filters_disabled": False,
        "single_select_field": single_select_field_1,
        "card_cover_image_field": cover_image_file_field_1,
    }

    kanban_view = ViewHandler().update_view(user, kanban_view, **original_kanban_data)

    assert kanban_view.name == original_kanban_data["name"]
    assert kanban_view.filter_type == original_kanban_data["filter_type"]
    assert kanban_view.filters_disabled == original_kanban_data["filters_disabled"]
    assert (
        kanban_view.single_select_field_id
        == original_kanban_data["single_select_field"].id
    )
    assert (
        kanban_view.card_cover_image_field_id
        == original_kanban_data["card_cover_image_field"].id
    )

    new_kanban_data = {
        "name": "Test New",
        "filter_type": "OR",
        "filters_disabled": True,
        "single_select_field": single_select_field_2,
        "card_cover_image_field": cover_image_file_field_2,
    }

    kanban_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user, kanban_view, **new_kanban_data
    )

    assert kanban_view.name == new_kanban_data["name"]
    assert kanban_view.filter_type == new_kanban_data["filter_type"]
    assert kanban_view.filters_disabled == new_kanban_data["filters_disabled"]
    assert (
        kanban_view.single_select_field_id == new_kanban_data["single_select_field"].id
    )
    assert (
        kanban_view.card_cover_image_field_id
        == new_kanban_data["card_cover_image_field"].id
    )

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(kanban_view.id)], session_id
    )

    kanban_view.refresh_from_db()
    assert_undo_redo_actions_are_valid(action_undone, [UpdateViewActionType])

    assert kanban_view.name == original_kanban_data["name"]
    assert kanban_view.filter_type == original_kanban_data["filter_type"]
    assert kanban_view.filters_disabled == original_kanban_data["filters_disabled"]
    assert (
        kanban_view.single_select_field_id
        == original_kanban_data["single_select_field"].id
    )
    assert (
        kanban_view.card_cover_image_field_id
        == original_kanban_data["card_cover_image_field"].id
    )

    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(kanban_view.id)], session_id
    )

    kanban_view.refresh_from_db()
    assert_undo_redo_actions_are_valid(action_redone, [UpdateViewActionType])

    assert kanban_view.name == new_kanban_data["name"]
    assert kanban_view.filter_type == new_kanban_data["filter_type"]
    assert kanban_view.filters_disabled == new_kanban_data["filters_disabled"]
    assert (
        kanban_view.single_select_field_id == new_kanban_data["single_select_field"].id
    )
    assert (
        kanban_view.card_cover_image_field_id
        == new_kanban_data["card_cover_image_field"].id
    )


@pytest.mark.django_db
def test_can_duplicate_kanban_view_with_cover_image(
    api_client, data_fixture, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    cover_image_file_field = data_fixture.create_file_field(table=table)
    kanban_view = premium_data_fixture.create_kanban_view(
        table=table, card_cover_image_field=cover_image_file_field
    )

    assert View.objects.count() == 1

    response = api_client.post(
        reverse("api:database:views:duplicate", kwargs={"view_id": kanban_view.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] != kanban_view.id
    assert response_json["name"] == f"{kanban_view.name} 2"
    assert response_json["card_cover_image_field"] == cover_image_file_field.id

    assert View.objects.count() == 2

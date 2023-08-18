from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import reverse
from django.test.utils import override_settings
from django.utils import timezone

import pytest
from baserow_premium.views.models import CalendarView, CalendarViewFieldOptions
from dateutil.tz import gettz
from freezegun import freeze_time
from pytz import utc
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_402_PAYMENT_REQUIRED,
    HTTP_404_NOT_FOUND,
)

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.fields.field_types import TextFieldType
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View
from baserow.test_utils.helpers import (
    AnyInt,
    is_dict_subset,
    setup_interesting_test_table,
)


def get_list_url(calendar_view_id: int) -> str:
    queryparams_ts_jan2023 = (
        f"from_timestamp={str(timezone.datetime(2023, 1, 1))}"
        f"&to_timestamp={str(timezone.datetime(2023, 2, 1))}"
    )
    return (
        reverse(
            "api:database:views:calendar:list", kwargs={"view_id": calendar_view_id}
        )
        + f"?{queryparams_ts_jan2023}"
    )


def get_public_list_url(calendar_view_slug: str) -> str:
    queryparams_ts_jan2023 = (
        f"from_timestamp={str(timezone.datetime(2023, 1, 1))}"
        f"&to_timestamp={str(timezone.datetime(2023, 2, 1))}"
    )
    return (
        reverse(
            "api:database:views:calendar:public_rows",
            kwargs={"slug": calendar_view_slug},
        )
        + f"?{queryparams_ts_jan2023}"
    )


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_list_without_valid_premium_license(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=False
    )
    calendar = premium_data_fixture.create_calendar_view(user=user)
    url = get_list_url(calendar.id)

    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})

    assert response.status_code == HTTP_402_PAYMENT_REQUIRED
    assert response.json()["error"] == "ERROR_FEATURE_NOT_AVAILABLE"

    # The calendar view should work if it's a template.

    premium_data_fixture.create_template(workspace=calendar.table.database.workspace)

    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})

    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_list_without_valid_premium_license_for_workspace(
    api_client, premium_data_fixture, alternative_per_workspace_license_service
):
    # without a license

    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    calendar = premium_data_fixture.create_calendar_view(user=user)
    alternative_per_workspace_license_service.restrict_user_premium_to(user, [0])
    url = get_list_url(calendar.id)

    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})

    assert response.status_code == HTTP_402_PAYMENT_REQUIRED
    assert response.json()["error"] == "ERROR_FEATURE_NOT_AVAILABLE"

    # with a valid license

    alternative_per_workspace_license_service.restrict_user_premium_to(
        user, [calendar.table.database.workspace.id]
    )
    premium_data_fixture.create_template(workspace=calendar.table.database.workspace)

    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})

    assert response.status_code == HTTP_200_OK


# authorization


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_list_rows_user_not_in_workspace(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        has_active_premium_license=True,
    )
    calendar = premium_data_fixture.create_calendar_view()
    url = get_list_url(calendar.id)

    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"


# invalid view


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_list_rows_invalid_view(api_client, premium_data_fixture):
    # view doesn't exist

    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        has_active_premium_license=True,
    )
    calendar = premium_data_fixture.create_calendar_view(user=user, date_field=None)
    url = get_list_url(0)

    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    # missing date field

    url = get_list_url(calendar.id)

    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_CALENDAR_VIEW_HAS_NO_DATE_FIELD"


# field options


@pytest.mark.django_db
@pytest.mark.view_calendar
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
    date_field = premium_data_fixture.create_date_field(table=table)
    calendar = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )
    url = get_list_url(calendar.id)

    response = api_client.get(
        f"{url}&include=field_options", **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["field_options"]) == 3
    assert response_json["field_options"][str(date_field.id)]["hidden"] is True
    assert response_json["field_options"][str(date_field.id)]["order"] == 32767
    assert response_json["field_options"][str(text_field.id)]["hidden"] is True
    assert response_json["field_options"][str(text_field.id)]["order"] == 32767
    assert response_json["field_options"][str(single_select_field.id)]["hidden"] is True
    assert response_json["field_options"][str(single_select_field.id)]["order"] == 32767


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_patch_calendar_view_field_options(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        has_active_premium_license=True,
    )
    table = premium_data_fixture.create_database_table(user=user)
    text_field = premium_data_fixture.create_text_field(table=table)
    calendar = premium_data_fixture.create_calendar_view(table=table, date_field=None)
    url = reverse("api:database:views:field_options", kwargs={"view_id": calendar.id})

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
    options = calendar.get_field_options()
    assert len(options) == 1
    assert options[0].field_id == text_field.id
    assert options[0].hidden is False
    assert options[0].order == 32767


# listing rows


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_list_all_rows(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    date_field = premium_data_fixture.create_date_field(
        table=table, date_include_time=True
    )
    calendar = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )
    datetime_from = timezone.datetime(2023, 1, 1)
    datetime_to = timezone.datetime(2023, 2, 1)
    queryparams_timestamps = (
        f"?from_timestamp={str(datetime_from)}" f"&to_timestamp={str(datetime_to)}"
    )
    datetimes = [
        timezone.datetime(2022, 12, 31),  # not in range
        timezone.datetime(2023, 1, 1),
        timezone.datetime(2023, 1, 10),
        timezone.datetime(2023, 1, 31),
        timezone.datetime(2023, 1, 31, 23, 59, 59, 999999),
        timezone.datetime(2023, 2, 1),  # not in range,
        None,  # not in range
    ]
    model = table.get_model()

    for datetime in datetimes:
        model.objects.create(
            **{
                f"field_{date_field.id}": datetime.replace(tzinfo=utc)
                if datetime is not None
                else None,
            }
        )

    url = (
        reverse("api:database:views:calendar:list", kwargs={"view_id": calendar.id})
        + queryparams_timestamps
    )
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["rows"]) == 31

    assert response_json["rows"].get("2022-12-31", None) is None

    assert response_json["rows"]["2023-01-01"]["count"] == 1
    assert len(response_json["rows"]["2023-01-01"]["results"]) == 1
    assert is_dict_subset(
        {
            f"field_{date_field.id}": "2023-01-01T00:00:00Z",
        },
        response_json["rows"]["2023-01-01"]["results"][0],
    )

    assert response_json["rows"]["2023-01-10"]["count"] == 1
    assert len(response_json["rows"]["2023-01-10"]["results"]) == 1
    assert is_dict_subset(
        {
            f"field_{date_field.id}": "2023-01-10T00:00:00Z",
        },
        response_json["rows"]["2023-01-10"]["results"][0],
    )

    assert response_json["rows"]["2023-01-31"]["count"] == 2
    assert len(response_json["rows"]["2023-01-31"]["results"]) == 2
    assert is_dict_subset(
        {
            f"field_{date_field.id}": "2023-01-31T00:00:00Z",
        },
        response_json["rows"]["2023-01-31"]["results"][0],
    )
    assert is_dict_subset(
        {
            f"field_{date_field.id}": "2023-01-31T23:59:59.999999Z",
        },
        response_json["rows"]["2023-01-31"]["results"][1],
    )

    assert response_json["rows"].get("2023-02-01", None) is None


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_list_all_rows_limit_offset(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    date_field = premium_data_fixture.create_date_field(
        table=table, date_include_time=True
    )
    calendar = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )
    datetime_from = timezone.datetime(2023, 1, 1)
    datetime_to = timezone.datetime(2023, 2, 1)
    queryparams_timestamps = (
        f"?from_timestamp={str(datetime_from)}" f"&to_timestamp={str(datetime_to)}"
    )
    queryparams_limit_offset = f"&limit=3&offset=2"
    datetimes = [
        timezone.datetime(2022, 12, 31),  # not in range
        timezone.datetime(2023, 1, 1),
        timezone.datetime(2023, 1, 10),
        timezone.datetime(2023, 1, 31),
        timezone.datetime(2023, 2, 1),  # not in range,
    ]
    model = table.get_model()

    for datetime in datetimes:
        for i in range(5):
            model.objects.create(
                **{
                    f"field_{date_field.id}": datetime.replace(hour=i, tzinfo=utc),
                }
            )

    url = (
        reverse("api:database:views:calendar:list", kwargs={"view_id": calendar.id})
        + queryparams_timestamps
        + queryparams_limit_offset
    )
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["rows"]) == 31

    assert response_json["rows"].get("2022-12-31", None) is None

    assert response_json["rows"]["2023-01-01"]["count"] == 5
    assert len(response_json["rows"]["2023-01-01"]["results"]) == 3
    assert is_dict_subset(
        {
            f"field_{date_field.id}": "2023-01-01T02:00:00Z",
        },
        response_json["rows"]["2023-01-01"]["results"][0],
    )

    assert response_json["rows"]["2023-01-10"]["count"] == 5
    assert len(response_json["rows"]["2023-01-10"]["results"]) == 3
    assert is_dict_subset(
        {
            f"field_{date_field.id}": "2023-01-10T02:00:00Z",
        },
        response_json["rows"]["2023-01-10"]["results"][0],
    )

    assert response_json["rows"]["2023-01-31"]["count"] == 5
    assert len(response_json["rows"]["2023-01-31"]["results"]) == 3
    assert is_dict_subset(
        {
            f"field_{date_field.id}": "2023-01-31T02:00:00Z",
        },
        response_json["rows"]["2023-01-31"]["results"][0],
    )

    assert response_json["rows"].get("2023-02-01", None) is None


@pytest.mark.parametrize(
    "from_timestamp,to_timestamp,error_field",
    [
        ("", "2023-01-10 03:00:00", "from_timestamp"),
        ("abc", "2023-01-10 03:00:00", "from_timestamp"),
        ("2023-01-10 03:00:00", "", "to_timestamp"),
        ("2023-01-10 03:00:00", "abc", "to_timestamp"),
    ],
)
@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_list_all_rows_invalid_from_to_timestamp(
    from_timestamp, to_timestamp, error_field, api_client, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    date_field = premium_data_fixture.create_date_field(
        table=table, date_include_time=True
    )
    calendar = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )
    queryparams_timestamps = (
        f"?from_timestamp={from_timestamp}" f"&to_timestamp={to_timestamp}"
    )

    url = (
        reverse("api:database:views:calendar:list", kwargs={"view_id": calendar.id})
        + queryparams_timestamps
    )
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["detail"][error_field][0]["code"] == "invalid"


@pytest.mark.parametrize(
    "limit,offset,error_field",
    [
        ("abc", "5", "limit"),
        ("", "5", "limit"),
        ("5", "", "offset"),
        ("5", "abc", "offset"),
    ],
)
@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_list_all_rows_invalid_limit_offset(
    limit, offset, error_field, api_client, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    date_field = premium_data_fixture.create_date_field(
        table=table, date_include_time=True
    )
    calendar = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )

    queryparams = f"?limit={limit}" f"&offset={offset}"

    url = (
        reverse("api:database:views:calendar:list", kwargs={"view_id": calendar.id})
        + queryparams
    )
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["detail"][error_field][0]["code"] == "invalid"


# creating and updating calendar view


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_create_calendar_view(api_client, premium_data_fixture):
    # date field doesn't belong to the table

    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    date_field = premium_data_fixture.create_date_field()

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "name": "Test 1",
            "type": "calendar",
            "filter_type": "OR",
            "filters_disabled": True,
            "date_field": date_field.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_FIELD_NOT_IN_TABLE"

    # date field is null

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "name": "Test 1",
            "type": "calendar",
            "filter_type": "OR",
            "filters_disabled": True,
            "date_field": None,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Test 1"
    assert response_json["type"] == "calendar"
    assert response_json["filter_type"] == "OR"
    assert response_json["filters_disabled"] is True
    assert response_json["date_field"] is None

    calendar_view = CalendarView.objects.all().last()
    assert calendar_view.id == response_json["id"]
    assert calendar_view.date_field_id is None

    # date field is set

    date_field = premium_data_fixture.create_date_field(table=table)

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "name": "Test 2",
            "type": "calendar",
            "filter_type": "AND",
            "filters_disabled": False,
            "date_field": date_field.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Test 2"
    assert response_json["type"] == "calendar"
    assert response_json["filter_type"] == "AND"
    assert response_json["filters_disabled"] is False
    assert response_json["date_field"] == date_field.id

    calendar_view = CalendarView.objects.all().last()
    assert calendar_view.id == response_json["id"]
    assert calendar_view.date_field_id == date_field.id


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_create_calendar_view_different_field_types(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table, _, _, _, context = setup_interesting_test_table(
        premium_data_fixture, user=user
    )
    kwargs = {
        "table": table,
        "name": premium_data_fixture.fake.name(),
        "order": 1,
    }

    specific_fields = [f.specific for f in table.field_set.all()]
    can_represent_date_fields = [
        f
        for f in specific_fields
        if field_type_registry.get_by_model(f).can_represent_date(f)
    ]

    for field in can_represent_date_fields:
        response = api_client.post(
            reverse("api:database:views:list", kwargs={"table_id": table.id}),
            {
                "name": "Test",
                "type": "calendar",
                "date_field": field.id,
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == HTTP_200_OK

    not_compatible_field_type = field_type_registry.get(TextFieldType.type)
    field = not_compatible_field_type.model_class.objects.create(**kwargs)
    premium_data_fixture.create_model_field(kwargs["table"], field)

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "name": "Test 2",
            "type": "calendar",
            "date_field": field.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_update_calendar_view(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    calendar_view = premium_data_fixture.create_calendar_view(
        table=table, date_field=None
    )
    date_field = premium_data_fixture.create_date_field(table=table)
    date_field_not_in_table = premium_data_fixture.create_date_field()

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": calendar_view.id}),
        {
            "date_field": date_field_not_in_table.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_FIELD_NOT_IN_TABLE"

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": calendar_view.id}),
        {
            "date_field": date_field.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["date_field"] == date_field.id

    calendar_view.refresh_from_db()
    assert calendar_view.date_field_id == date_field.id

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": calendar_view.id}),
        {
            "date_field": None,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["date_field"] is None

    calendar_view.refresh_from_db()
    assert calendar_view.date_field is None


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_list_all_rows_with_field_timezone_set_uses_field_timezone(
    api_client, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    date_field = premium_data_fixture.create_date_field(
        table=table, date_include_time=True, date_force_timezone="Australia/Melbourne"
    )
    calendar = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )

    melbourne_tz = gettz("Australia/Melbourne")
    datetime_from = timezone.datetime(2023, 1, 1, tzinfo=melbourne_tz)
    datetime_to = timezone.datetime(2023, 1, 2, tzinfo=melbourne_tz)
    queryparams_timestamps = {
        "from_timestamp": datetime_from.isoformat(),
        "to_timestamp": datetime_to.isoformat(),
    }
    outside_to_from_period = datetime_from - timezone.timedelta(hours=1)
    inside_to_from_period = datetime_from + timezone.timedelta(hours=1)
    model = table.get_model()

    row1 = model.objects.create(
        **{f"field_{date_field.id}": inside_to_from_period.astimezone(tz=utc)}
    )
    row2 = model.objects.create(
        **{f"field_{date_field.id}": outside_to_from_period.astimezone(tz=utc)}
    )

    url = (
        reverse("api:database:views:calendar:list", kwargs={"view_id": calendar.id})
        + "?"
        + urlencode(queryparams_timestamps)
    )
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK, response_json

    assert response_json["rows"] == {
        "2023-01-01": {
            "count": 1,
            "results": [
                {
                    f"field_{date_field.id}": "2022-12-31T14:00:00Z",
                    "id": row1.id,
                    "order": "1.00000000000000000000",
                }
            ],
        }
    }


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_list_all_rows_with_user_timezone_set_uses_user_timezone_when_no_field_tz(
    api_client, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    date_field = premium_data_fixture.create_date_field(
        table=table, date_include_time=True
    )
    calendar = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )

    tz_name = "Australia/Melbourne"
    melbourne_tz = gettz(tz_name)
    datetime_from = timezone.datetime(2023, 1, 1, tzinfo=melbourne_tz)
    datetime_to = timezone.datetime(2023, 1, 2, tzinfo=melbourne_tz)
    queryparams_timestamps = {
        "from_timestamp": datetime_from.isoformat(),
        "to_timestamp": datetime_to.isoformat(),
        "user_timezone": tz_name,
    }
    outside_to_from_period = datetime_from - timezone.timedelta(hours=1)
    inside_to_from_period = datetime_from + timezone.timedelta(hours=1)
    model = table.get_model()

    row1 = model.objects.create(
        **{f"field_{date_field.id}": inside_to_from_period.astimezone(tz=utc)}
    )
    row2 = model.objects.create(
        **{f"field_{date_field.id}": outside_to_from_period.astimezone(tz=utc)}
    )

    url = (
        reverse("api:database:views:calendar:list", kwargs={"view_id": calendar.id})
        + "?"
        + urlencode(queryparams_timestamps)
    )
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK, response_json

    assert response_json["rows"] == {
        "2023-01-01": {
            "count": 1,
            "results": [
                {
                    f"field_{date_field.id}": "2022-12-31T14:00:00Z",
                    "id": row1.id,
                    "order": "1.00000000000000000000",
                }
            ],
        }
    }


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_invalid_user_timezone_returns_error(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    date_field = premium_data_fixture.create_date_field(
        table=table,
        date_include_time=True,
    )
    calendar = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )

    response = api_client.get(
        get_list_url(calendar.id) + "&user_timezone=NONSENSE",
        **{"HTTP_AUTHORIZATION": f"JWT" f" {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json == {
        "detail": {
            "user_timezone": [
                {
                    "code": "invalid_choice",
                    "error": '"NONSENSE" is not a valid choice.',
                }
            ]
        },
        "error": "ERROR_QUERY_PARAMETER_VALIDATION",
    }


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_too_wide_timerange_returns_error(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    date_field = premium_data_fixture.create_date_field(
        table=table,
        date_include_time=True,
    )
    calendar = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )
    datetime_from = timezone.datetime(2023, 1, 1)
    datetime_to = datetime_from + timezone.timedelta(
        days=settings.MAX_NUMBER_CALENDAR_DAYS + 1
    )
    queryparams_timestamps = {
        "from_timestamp": datetime_from.isoformat(),
        "to_timestamp": datetime_to.isoformat(),
    }

    response = api_client.get(
        reverse("api:database:views:calendar:list", kwargs={"view_id": calendar.id})
        + "?"
        + urlencode(queryparams_timestamps),
        **{"HTTP_AUTHORIZATION": f"JWT" f" {token}"},
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json == {
        "detail": {
            "non_field_errors": [
                {
                    "code": "invalid",
                    "error": "the number of days between "
                    "from_timestamp and to_timestamp "
                    f"must be less than {settings.MAX_NUMBER_CALENDAR_DAYS} days",
                }
            ]
        },
        "error": "ERROR_QUERY_PARAMETER_VALIDATION",
    }


@pytest.mark.django_db
@pytest.mark.view_calendar
def test_can_duplicate_calendar_view_with_date_field(
    api_client, data_fixture, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    date_field = data_fixture.create_date_field(table=table)
    calendar_view = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )

    assert View.objects.count() == 1

    response = api_client.post(
        reverse("api:database:views:duplicate", kwargs={"view_id": calendar_view.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] != calendar_view.id
    assert response_json["name"] == f"{calendar_view.name} 2"
    assert response_json["date_field"] == date_field.id
    assert View.objects.count() == 2


@pytest.mark.django_db
def test_get_public_calendar_view_with_single_select_and_cover(
    api_client, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token()
    table = premium_data_fixture.create_database_table(user=user)
    date_field = premium_data_fixture.create_date_field(table=table, order=0)
    calendar_view = premium_data_fixture.create_calendar_view(
        table=table, user=user, public=True, date_field=date_field
    )
    date_field = calendar_view.date_field
    public_field = premium_data_fixture.create_text_field(
        table=table, name="public", order=1
    )
    hidden_field = premium_data_fixture.create_text_field(
        table=table, name="hidden", order=2
    )

    premium_data_fixture.create_calendar_view_field_option(
        calendar_view, date_field, hidden=False, order=0
    )
    premium_data_fixture.create_calendar_view_field_option(
        calendar_view, public_field, hidden=False, order=1
    )
    premium_data_fixture.create_calendar_view_field_option(
        calendar_view, hidden_field, hidden=True, order=2
    )

    # Can access as an anonymous user
    response = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": calendar_view.slug})
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK, response_json
    assert response_json == {
        "fields": [
            {
                "id": date_field.id,
                "name": date_field.name,
                "order": 0,
                "primary": date_field.primary,
                "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                "type": "date",
                "read_only": False,
                "date_force_timezone": None,
                "date_format": "EU",
                "date_include_time": False,
                "date_show_tzinfo": False,
                "date_time_format": "24",
            },
            {
                "id": public_field.id,
                "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                "name": "public",
                "order": 1,
                "primary": False,
                "text_default": "",
                "type": "text",
                "read_only": False,
            },
        ],
        "view": {
            "id": calendar_view.slug,
            "name": calendar_view.name,
            "order": 0,
            "public": True,
            "slug": calendar_view.slug,
            "sortings": [],
            "table": {
                "database_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                "id": PUBLIC_PLACEHOLDER_ENTITY_ID,
            },
            "type": "calendar",
            "date_field": date_field.id,
            "show_logo": True,
        },
    }


@pytest.mark.django_db
def test_list_public_rows_without_date_field(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token()
    table = premium_data_fixture.create_database_table(user=user)

    calendar_view = premium_data_fixture.create_calendar_view(
        table=table, user=user, public=True, date_field=None
    )

    # Get access as an anonymous user
    response = api_client.get(
        get_public_list_url(calendar_view.slug),
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_CALENDAR_VIEW_HAS_NO_DATE_FIELD"


@pytest.mark.django_db
def test_list_public_rows_without_password(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token()
    table = premium_data_fixture.create_database_table(user=user)

    calendar_view = premium_data_fixture.create_calendar_view(
        table=table,
        user=user,
        public=True,
    )
    calendar_view.set_password("test")
    calendar_view.save()

    response = api_client.get(
        get_public_list_url(calendar_view.slug),
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_list_public_rows_with_valid_password(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token()
    table = premium_data_fixture.create_database_table(user=user)

    calendar_view = premium_data_fixture.create_calendar_view(
        table=table,
        user=user,
        public=True,
    )
    calendar_view.set_password("test")
    calendar_view.save()

    token = ViewHandler().encode_public_view_token(calendar_view)
    response = api_client.get(
        get_public_list_url(calendar_view.slug),
        HTTP_BASEROW_VIEW_AUTHORIZATION=f"JWT {token}",
        format="json",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_list_public_rows_password_protected_with_jwt_auth(
    api_client, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token()
    table = premium_data_fixture.create_database_table(user=user)

    calendar_view = premium_data_fixture.create_calendar_view(
        table=table,
        user=user,
        public=True,
    )
    calendar_view.set_password("test")
    calendar_view.save()

    response = api_client.get(
        get_public_list_url(calendar_view.slug),
        HTTP_AUTHORIZATION=f"JWT {token}",
        format="json",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_list_public_rows_doesnt_show_hidden_columns(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token()
    table = premium_data_fixture.create_database_table(user=user)

    date_field = premium_data_fixture.create_date_field(table=table, name="date")
    calendar_view = premium_data_fixture.create_calendar_view(
        table=table, user=user, public=True, date_field=date_field
    )

    # Only information related the public field should be returned
    public_field = premium_data_fixture.create_text_field(table=table, name="public")
    hidden_field = premium_data_fixture.create_text_field(table=table, name="hidden")

    date_field_options = CalendarViewFieldOptions.objects.get(
        field_id=calendar_view.date_field_id
    )
    public_field_option = premium_data_fixture.create_calendar_view_field_option(
        calendar_view, public_field, hidden=False
    )
    premium_data_fixture.create_calendar_view_field_option(
        calendar_view, hidden_field, hidden=True
    )

    with freeze_time("2023-01-10 12:00"):
        row = RowHandler().create_row(
            user, table, values={f"field_{date_field.id}": "2023-01-10 12:00"}
        )

        # Get access as an anonymous user
        response = api_client.get(
            get_public_list_url(calendar_view.slug) + "&include=field_options"
        )
        response_json = response.json()
        assert response.status_code == HTTP_200_OK
        assert response_json["field_options"] == {
            f"{public_field.id}": {
                "hidden": False,
                "order": public_field_option.order,
            },
            f"{calendar_view.date_field_id}": {
                "hidden": True,
                "order": date_field_options.order,
            },
        }
        day_with_row = response_json["rows"].pop("2023-01-10")
        assert day_with_row["count"] == 1
        assert day_with_row["results"] == [
            {
                f"field_{date_field.id}": "2023-01-10",
                f"field_{public_field.id}": None,
                "id": row.id,
                "order": str(row.order),
            }
        ]
        for other_day in response_json["rows"].values():
            assert other_day["count"] == 0


@pytest.mark.django_db
def test_list_public_rows_limit_offset(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token()
    table = premium_data_fixture.create_database_table(user=user)

    date_field = premium_data_fixture.create_date_field(
        table=table, name="date", date_include_time=True
    )
    calendar_view = premium_data_fixture.create_calendar_view(
        table=table,
        user=user,
        public=True,
        date_field=date_field,
    )

    with freeze_time("2023-01-10 12:00"):
        for day in range(10):
            for hour in range(10):
                row = RowHandler().create_row(
                    user,
                    table,
                    values={f"field_{date_field.id}": f"2023-01-{day+10} {hour+10}:00"},
                )

        response = api_client.get(
            get_public_list_url(calendar_view.slug) + f"&limit=3&offset=5"
        )
        response_json = response.json()
        assert response.status_code == HTTP_200_OK
        day_with_row = response_json["rows"].pop("2023-01-10")
        assert day_with_row["count"] == 10
        assert len(day_with_row["results"]) == 3
        assert [d[f"field_{date_field.id}"] for d in day_with_row["results"]] == [
            "2023-01-10T15:00:00Z",
            "2023-01-10T16:00:00Z",
            "2023-01-10T17:00:00Z",
        ]


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_search_calendar_rows(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)

    date_field = premium_data_fixture.create_date_field(table=table, name="date")
    description_field = premium_data_fixture.create_text_field(
        table=table, name="description"
    )

    calendar = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )

    rows_data = [
        ["2023-01-01", "Meeting with team"],
        ["2023-01-02", "Lunch with client"],
        ["2023-01-02", "Meeting with client"],
        ["2023-01-02", "Meeting with employees"],
        ["2023-01-12", "Team building activity"],
    ]
    premium_data_fixture.create_rows_in_table(
        table=table, rows=rows_data, fields=[date_field, description_field]
    )

    url = get_list_url(calendar.id) + "&search=client"
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    expected_data = {
        "2023-01-02": {
            "count": 2,
            "results": [
                {
                    "id": AnyInt(),
                    "order": "1.00000000000000000000",
                    description_field.db_column: "Lunch with client",
                    date_field.db_column: "2023-01-02",
                },
                {
                    "id": AnyInt(),
                    "order": "1.00000000000000000000",
                    description_field.db_column: "Meeting with client",
                    date_field.db_column: "2023-01-02",
                },
            ],
        }
    }

    results_for_searched_day = response_json["rows"].get("2023-01-02", {})
    assert results_for_searched_day == expected_data["2023-01-02"]


@pytest.mark.django_db
@pytest.mark.view_calendar
@override_settings(DEBUG=True)
def test_search_calendar_with_empty_term(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)

    date_field = premium_data_fixture.create_date_field(table=table, name="date")
    description_field = premium_data_fixture.create_text_field(
        table=table, name="description"
    )

    calendar = premium_data_fixture.create_calendar_view(
        table=table, date_field=date_field
    )

    rows_data = [
        ["2023-01-01", "Meeting with team"],
        ["2023-01-02", "Lunch with client"],
        ["2023-01-02", "Meeting with client"],
        ["2023-01-02", "Meeting with employees"],
        ["2023-01-12", "Team building activity"],
    ]
    premium_data_fixture.create_rows_in_table(
        table=table, rows=rows_data, fields=[date_field, description_field]
    )

    url = get_list_url(calendar.id) + "&search="
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")

    assert response.status_code == HTTP_200_OK

    total_results = sum(
        [date_data["count"] for date_data in response.json()["rows"].values()]
    )

    assert total_results == 5

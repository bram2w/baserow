from contextlib import contextmanager
from decimal import Decimal
from ipaddress import ip_network
from socket import AF_INET, AF_INET6, IPPROTO_TCP, SOCK_STREAM
from typing import Any, Dict, List, Optional, Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import connection
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import make_aware, utc

import psycopg2
from freezegun import freeze_time
from pytest_unordered import unordered

from baserow.contrib.database.fields.field_helpers import (
    construct_all_possible_field_kwargs,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import SelectOption
from baserow.contrib.database.models import Database
from baserow.contrib.database.rows.handler import RowHandler
from baserow.core.action.models import Action
from baserow.core.action.registries import ActionType
from baserow.core.models import Group

User = get_user_model()


def _parse_datetime(datetime):
    return make_aware(parse_datetime(datetime), timezone=utc)


def _parse_date(date):
    return parse_date(date)


def is_dict_subset(subset: dict, superset: dict) -> bool:
    if isinstance(subset, dict):
        return all(
            key in superset and is_dict_subset(val, superset[key])
            for key, val in subset.items()
        )

    if isinstance(subset, list) or isinstance(subset, set):
        return all(
            any(is_dict_subset(subitem, superitem) for superitem in superset)
            for subitem in subset
        )

    return subset == superset


def setup_interesting_test_table(
    data_fixture,
    user: Optional[AbstractUser] = None,
    database: Optional[Database] = None,
    name: Optional[str] = None,
    file_suffix: Optional[str] = None,
    user_kwargs: Optional[Dict[str, Any]] = None,
):
    """
    Constructs a testing table with every field type, their sub types and any other
    interesting baserow edge cases worth testing when writing a comprehensive "does this
    feature work with all the baserow fields" test.

    :param data_fixture: The baserow testing data_fixture object
    :return:
    """

    if user_kwargs is None:
        user_kwargs = {}

    user = user or data_fixture.create_user(**user_kwargs)
    database = database or data_fixture.create_database_application(user=user)
    user2 = User.objects.filter(
        email="user2@example.com"
    ).first() or data_fixture.create_user(
        group=database.group, email="user2@example.com"
    )
    user3 = User.objects.filter(
        email="user3@example.com"
    ).first() or data_fixture.create_user(
        group=database.group, email="user3@example.com"
    )
    table = data_fixture.create_database_table(
        database=database, user=user, name=name or "interesting_test_table"
    )
    link_table = data_fixture.create_database_table(
        database=database, user=user, name="link_table"
    )
    other_table_primary_text_field = data_fixture.create_text_field(
        table=link_table, name="text_field", primary=True
    )
    decimal_link_table = data_fixture.create_database_table(
        database=database, user=user, name="decimal_link_table"
    )
    file_link_table = data_fixture.create_database_table(
        database=database, user=user, name="file_link_table"
    )
    handler = FieldHandler()
    all_possible_kwargs_per_type = construct_all_possible_field_kwargs(
        table, link_table, decimal_link_table, file_link_table
    )
    name_to_field_id = {}
    i = 0
    other_table_primary_decimal_field = data_fixture.create_number_field(
        table=decimal_link_table,
        name="text_field",
        primary=True,
        number_decimal_places=3,
        number_negative=True,
    )
    other_table_primary_file_field = data_fixture.create_file_field(
        table=file_link_table,
        name="file_field",
        primary=True,
    )
    for field_type_name, all_possible_kwargs in all_possible_kwargs_per_type.items():
        for kwargs in all_possible_kwargs:
            field = handler.create_field(
                user=user,
                table=table,
                type_name=field_type_name,
                order=i,
                **kwargs,
            )
            i += 1
            name_to_field_id[kwargs["name"]] = field.id
    row_handler = RowHandler()

    model = table.get_model()
    datetime = _parse_datetime("2020-02-01 01:23")
    date = _parse_date("2020-02-01")

    values = {
        "text": "text",
        "long_text": "long_text",
        "url": "https://www.google.com",
        "email": "test@example.com",
        "negative_int": -1,
        "positive_int": 1,
        "negative_decimal": Decimal("-1.2"),
        "positive_decimal": Decimal("1.2"),
        "rating": 3,
        "boolean": "True",
        "datetime_us": datetime,
        "date_us": date,
        "datetime_eu": datetime,
        "date_eu": date,
        "datetime_eu_tzone_visible": datetime,
        "datetime_eu_tzone_hidden": datetime,
        "last_modified_datetime_us": None,
        "last_modified_date_us": None,
        "last_modified_datetime_eu": None,
        "last_modified_date_eu": None,
        "last_modified_datetime_eu_tzone": None,
        "created_on_datetime_us": None,
        "created_on_date_us": None,
        "created_on_datetime_eu": None,
        "created_on_date_eu": None,
        "created_on_datetime_eu_tzone": None,
        # We will setup link rows manually later
        "link_row": None,
        "self_link_row": None,
        "link_row_without_related": None,
        "decimal_link_row": None,
        "file_link_row": None,
        "file": [
            {
                "name": "hashed_name.txt",
                "visible_name": "a.txt",
                "is_image": False,
                "size": 0,
                "mime_type": "text/plain",
                "image_width": 0,
                "image_height": 0,
                "uploaded_at": "2020-02-01 01:23",
            },
            {
                "name": "other_name.txt",
                "visible_name": "b.txt",
                "is_image": False,
                "size": 0,
                "mime_type": "text/plain",
                "image_width": 0,
                "image_height": 0,
                "uploaded_at": "2020-02-01 01:23",
            },
        ],
        "single_select": SelectOption.objects.get(
            value="A", field_id=name_to_field_id["single_select"]
        ),
        "multiple_select": None,
        "multiple_collaborators": None,
        "phone_number": "+4412345678",
        "formula_text": "test FORMULA",
        "formula_int": "1",
        "formula_bool": "true",
        "formula_decimal": "1.23",
        "formula_dateinterval": "",
        "formula_date": "2020-01-01",
        "formula_singleselect": "",
        "formula_email": "test@example.com",
        "formula_link_url_only": "",
        "formula_link_with_label": "",
    }

    with freeze_time("2020-02-01 01:23"):
        data_fixture.create_user_file(
            original_name=f"a.txt",
            unique=f"hashed{file_suffix}",
            sha256_hash="name",
        )
        data_fixture.create_user_file(
            original_name=f"b.txt",
            unique=f"other{file_suffix}",
            sha256_hash="name",
        )

    missing_fields = set(name_to_field_id.keys()) - set(values.keys()) - {"lookup"}
    assert missing_fields == set(), (
        "Please update the dictionary above with interesting test values for your new "
        f"field type. In the values dict you are missing the fields {missing_fields}."
    )
    row_values = {}
    for field_type, val in values.items():
        if val is not None:
            row_values[f"field_{name_to_field_id[field_type]}"] = val
    # Make a blank row to test empty field conversion also.

    # We freeze time here so that we know what the values of the last_modified and
    # created_on field types are going to be. Freezing the datetime will also freeze
    # the current daylight savings time information.
    with freeze_time("2021-01-02 12:00"):
        blank_row = row_handler.create_row(user, table, {})
        row = model.objects.create(**row_values)

    # Setup the link rows
    linked_row_1 = row_handler.create_row(
        user=user,
        table=link_table,
        values={
            other_table_primary_text_field.id: "linked_row_1",
        },
    )
    linked_row_2 = row_handler.create_row(
        user=user,
        table=link_table,
        values={
            other_table_primary_text_field.id: "linked_row_2",
        },
    )
    linked_row_3 = row_handler.create_row(
        user=user,
        table=link_table,
        values={
            other_table_primary_text_field.id: None,
        },
    )
    linked_row_4 = row_handler.create_row(
        user=user,
        table=decimal_link_table,
        values={
            other_table_primary_decimal_field.id: "1.234",
        },
    )
    linked_row_5 = row_handler.create_row(
        user=user,
        table=decimal_link_table,
        values={
            other_table_primary_decimal_field.id: "-123.456",
        },
    )
    linked_row_6 = row_handler.create_row(
        user=user,
        table=decimal_link_table,
        values={
            other_table_primary_decimal_field.id: None,
        },
    )
    file_suffix = file_suffix or ""
    with freeze_time("2020-01-01 12:00"):
        user_file_1 = data_fixture.create_user_file(
            original_name=f"name{file_suffix}.txt",
            unique=f"test{file_suffix}",
            sha256_hash=f"hash{file_suffix}",
        )
    linked_row_7 = row_handler.create_row(
        user=user,
        table=file_link_table,
        values={
            other_table_primary_file_field.id: [{"name": user_file_1.name}],
        },
    )
    linked_row_8 = row_handler.create_row(
        user=user,
        table=file_link_table,
        values={
            other_table_primary_file_field.id: None,
        },
    )

    link_row_field_id = name_to_field_id["link_row"]
    link_row_field_without_related_id = name_to_field_id["link_row_without_related"]
    self_link_row_field_id = name_to_field_id["self_link_row"]
    decimal_row_field_id = name_to_field_id["decimal_link_row"]
    file_link_row_id = name_to_field_id["file_link_row"]
    with freeze_time("2021-01-02 12:00"):
        handler = RowHandler()
        row = handler.update_row_by_id(
            user,
            table,
            row.id,
            {
                f"field_{link_row_field_id}": [
                    linked_row_1.id,
                    linked_row_2.id,
                    linked_row_3.id,
                ],
                f"field_{self_link_row_field_id}": [blank_row.id],
                f"field_{link_row_field_without_related_id}": [
                    linked_row_1.id,
                    linked_row_2.id,
                ],
                f"field_{decimal_row_field_id}": [
                    linked_row_4.id,
                    linked_row_5.id,
                    linked_row_6.id,
                ],
                f"field_{file_link_row_id}": [linked_row_7.id, linked_row_8.id],
            },
        )

    # multiple select
    getattr(row, f"field_{name_to_field_id['multiple_select']}").add(
        SelectOption.objects.get(
            value="D", field_id=name_to_field_id["multiple_select"]
        ).id
    )
    getattr(row, f"field_{name_to_field_id['multiple_select']}").add(
        SelectOption.objects.get(
            value="C", field_id=name_to_field_id["multiple_select"]
        ).id
    )
    getattr(row, f"field_{name_to_field_id['multiple_select']}").add(
        SelectOption.objects.get(
            value="E", field_id=name_to_field_id["multiple_select"]
        ).id
    )

    # multiple collaborators
    getattr(row, f"field_{name_to_field_id['multiple_collaborators']}").add(user2.id)
    getattr(row, f"field_{name_to_field_id['multiple_collaborators']}").add(user3.id)

    context = {"user2": user2, "user3": user3}

    return table, user, row, blank_row, context


def setup_interesting_test_database(
    data_fixture,
    user: Optional[AbstractUser] = None,
    group: Optional[Group] = None,
    database: Optional[Database] = None,
    name: Optional[str] = None,
    user_kwargs=None,
):
    if user_kwargs is None:
        user_kwargs = {}

    user = user or data_fixture.create_user(**user_kwargs)
    database = database or data_fixture.create_database_application(
        user=user, group=group, name=name
    )

    for table_name in ["A", "B", "C"]:
        setup_interesting_test_table(
            data_fixture,
            user=user,
            database=database,
            name=table_name,
            file_suffix=table_name,
        )

    return database


@contextmanager
def register_instance_temporarily(registry, instance):
    """
    A context manager to allow tests to register a new instance into a Baserow
    registry which will then unregister the instance afterwards to ensure the global
    registries are kept clean between tests.
    """

    registry.register(instance)
    try:
        yield instance
    finally:
        registry.unregister(instance)


def assert_undo_redo_actions_are_valid(
    actions: List[Action], expected_action_types: List[Type[ActionType]]
):
    assert len(actions) == len(
        expected_action_types
    ), f"Expected {len(actions)} actions but got {len(expected_action_types)} action_types"

    for action, expected_action_type in zip(actions, expected_action_types):
        assert (
            action.type == expected_action_type.type
        ), f"Action expected of type {expected_action_type} but got {action.type}"
        assert (
            action is not None
        ), f"Action is None, but should be of type {expected_action_type}"
        assert action.error is None, f"Action has error: {action.error}"


def assert_undo_redo_actions_fails_with_error(
    actions: List[Action], expected_action_types: List[Type[ActionType]]
):
    assert actions, "Actions list should not be empty"

    for action, expected_action_type in zip(actions, expected_action_types):
        assert action, f"Action is None, but should be of type {expected_action_type}"
        assert action.error is not None, "Action has no error, but should have one"


@contextmanager
def independent_test_db_connection():
    d = connection.settings_dict
    conn = psycopg2.connect(
        host=d["HOST"],
        database=d["NAME"],
        user=d["USER"],
        password=d["PASSWORD"],
        port=d["PORT"],
    )
    conn.autocommit = False
    yield conn
    conn.close()


def assert_serialized_field_values_are_the_same(
    value_1, value_2, ordered=False, field_name=None
):
    if isinstance(value_1, list) and not ordered:
        assert unordered(value_1, value_2)
    else:
        assert value_1 == value_2, f"{field_name or 'error'}: {value_1} != {value_2}"


def extract_serialized_field_value(field_value):
    if not field_value:
        return field_value

    def extract_value(value):
        if isinstance(value, dict):
            if "name" in value:
                return value["name"]
            if "url" in value:
                return (value.get("label") or "") + " (" + value["url"] + ")"
            return value["value"]
        return value

    if isinstance(field_value, list):
        return [extract_value(value) for value in field_value]

    return extract_value(field_value)


def assert_serialized_rows_contain_same_values(row_1, row_2):
    for field_name, row_field_value in row_1.items():
        row_1_value = extract_serialized_field_value(row_field_value)
        row_2_value = extract_serialized_field_value(row_2[field_name])
        assert_serialized_field_values_are_the_same(
            row_1_value, row_2_value, field_name=field_name
        )


# The httpretty stub implementation of socket.getaddrinfo is incorrect and doesn't
# return an IP causing advocate to fail, instead we patch to fix this.
def stub_getaddrinfo(host, port, family=None, socktype=None, proto=None, flags=None):
    try:
        ip_network(host)
        ip = host
    except ValueError:
        ip = "1.1.1.1"
    return [
        (AF_INET, SOCK_STREAM, IPPROTO_TCP, host, (ip, port)),
        (AF_INET6, SOCK_STREAM, IPPROTO_TCP, "", (ip, port)),
    ]


class AnyInt(int):
    """
    A class that can be used to check if a value is an int. Useful in tests when
    you don't care about ID, but you want to check all other values.
    """

    def __eq__(self, other):
        return isinstance(other, int)

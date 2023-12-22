from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from baserow.contrib.database.rows.actions import UpdateRowsActionType
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.rows.history import RowHistoryHandler
from baserow.contrib.database.rows.models import RowHistory
from baserow.contrib.database.rows.registries import (
    ChangeRowHistoryType,
    change_row_history_registry,
)
from baserow.core.action.registries import action_type_registry


@pytest.mark.django_db
@pytest.mark.row_history
def test_update_rows_insert_multiple_entries_in_row_history(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(
        name="Test", user=user, database=database
    )
    name_field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )

    row_handler = RowHandler()

    row_one = row_handler.create_row(user, table, {name_field.id: "Original 1"})
    row_two = row_handler.create_row(user, table, {name_field.id: "Original 2"})

    with freeze_time("2021-01-01 12:00"):
        action_type_registry.get_by_type(UpdateRowsActionType).do(
            user,
            table,
            [
                {"id": row_one.id, f"field_{name_field.id}": "New 1"},
                {"id": row_two.id, f"field_{name_field.id}": "New 2"},
            ],
        )
    assert RowHistory.objects.count() == 2

    history_entries = RowHistory.objects.order_by("row_id").values(
        "user_id",
        "user_name",
        "table_id",
        "row_id",
        "action_timestamp",
        "action_type",
        "before_values",
        "after_values",
        "fields_metadata",
    )

    assert list(history_entries) == [
        {
            "user_id": user.id,
            "user_name": user.first_name,
            "table_id": table.id,
            "row_id": row_one.id,
            "action_timestamp": datetime(2021, 1, 1, 12, 0, tzinfo=timezone.utc),
            "action_type": "update_rows",
            "before_values": {f"field_{name_field.id}": "Original 1"},
            "after_values": {f"field_{name_field.id}": "New 1"},
            "fields_metadata": {
                f"field_{name_field.id}": {
                    "type": "text",
                    "id": name_field.id,
                }
            },
        },
        {
            "user_id": user.id,
            "user_name": user.first_name,
            "table_id": table.id,
            "row_id": row_two.id,
            "action_timestamp": datetime(2021, 1, 1, 12, 0, tzinfo=timezone.utc),
            "action_type": "update_rows",
            "before_values": {f"field_{name_field.id}": "Original 2"},
            "after_values": {f"field_{name_field.id}": "New 2"},
            "fields_metadata": {
                f"field_{name_field.id}": {
                    "type": "text",
                    "id": name_field.id,
                }
            },
        },
    ]


@pytest.mark.django_db
@pytest.mark.row_history
def test_history_handler_only_save_changed_fields(data_fixture):
    user = data_fixture.create_user()
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

    row = row_handler.create_row(user, table, {name_field.id: "Original 1"})

    with freeze_time("2021-01-01 12:00"):
        action_type_registry.get_by_type(UpdateRowsActionType).do(
            user,
            table,
            [
                {
                    "id": row.id,
                    f"field_{name_field.id}": "New 1",
                    f"field_{number_field.id}": None,
                }
            ],
        )

    assert RowHistory.objects.count() == 1

    history_entries = RowHistory.objects.values(
        "user_id",
        "user_name",
        "table_id",
        "row_id",
        "action_timestamp",
        "action_type",
        "before_values",
        "after_values",
        "fields_metadata",
    )

    assert list(history_entries) == [
        {
            "user_id": user.id,
            "user_name": user.first_name,
            "table_id": table.id,
            "row_id": row.id,
            "action_timestamp": datetime(2021, 1, 1, 12, 0, tzinfo=timezone.utc),
            "action_type": "update_rows",
            "before_values": {
                f"field_{name_field.id}": "Original 1",
            },
            "after_values": {f"field_{name_field.id}": "New 1"},
            "fields_metadata": {
                f"field_{name_field.id}": {
                    "type": "text",
                    "id": name_field.id,
                }
            },
        },
    ]


@pytest.mark.django_db
@pytest.mark.row_history
def test_update_rows_action_doesnt_insert_entries_if_row_doesnt_change(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(
        name="Test", user=user, database=database
    )
    name_field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )

    row_handler = RowHandler()

    row_one = row_handler.create_row(user, table, {name_field.id: "Original 1"})
    row_two = row_handler.create_row(user, table, {name_field.id: "Original 2"})

    with freeze_time("2021-01-01 12:00"):
        action_type_registry.get_by_type(UpdateRowsActionType).do(
            user,
            table,
            [
                {"id": row_one.id, f"field_{name_field.id}": "New 1"},
                {"id": row_two.id, f"field_{name_field.id}": "Original 2"},
            ],
        )

    # This does not insert any entries in the row history table because no values
    # have changed.
    with freeze_time("2021-01-01 12:00"):
        action_type_registry.get_by_type(UpdateRowsActionType).do(
            user,
            table,
            [{"id": row_one.id, f"field_{name_field.id}": "New 1"}],
        )

    assert RowHistory.objects.count() == 1
    history_entries = RowHistory.objects.order_by("row_id").values(
        "user_id",
        "user_name",
        "table_id",
        "row_id",
        "action_timestamp",
        "action_type",
        "before_values",
        "after_values",
        "fields_metadata",
    )
    assert list(history_entries) == [
        {
            "user_id": user.id,
            "user_name": user.first_name,
            "table_id": table.id,
            "row_id": row_one.id,
            "action_timestamp": datetime(2021, 1, 1, 12, 0, tzinfo=timezone.utc),
            "action_type": "update_rows",
            "before_values": {f"field_{name_field.id}": "Original 1"},
            "after_values": {f"field_{name_field.id}": "New 1"},
            "fields_metadata": {
                f"field_{name_field.id}": {
                    "type": "text",
                    "id": name_field.id,
                }
            },
        }
    ]


@pytest.mark.django_db
@pytest.mark.row_history
def test_row_history_handler_list_history_filters_with_registry(data_fixture):
    """
    Test that queryset filtering is sourced from RowHistoryOperationsRegistry.
    """

    class FilterRowHistoryStub(ChangeRowHistoryType):
        type = "row_history_op_stub"

        def apply_to_list_queryset(self, queryset, workspace, table_id, row_id):
            return queryset.filter(user_id__lt=2)

    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(
        name="Test", user=user, database=database
    )
    common_params = {
        "table": table,
        "row_id": 999,
        "action_uuid": "uuid",
        "action_command_type": "cmd",
        "action_type": "type",
        "field_names": [],
        "fields_metadata": {},
        "before_values": {},
        "after_values": {},
        "action_timestamp": datetime(2021, 1, 3, 23, 59, tzinfo=timezone.utc),
    }
    entries = [RowHistory(**common_params, user_id=i) for i in range(0, 10)]
    RowHistory.objects.bulk_create(entries)
    assert (
        len(
            RowHistoryHandler().list_row_history(
                database.workspace, table.id, row_id=999
            )
        )
        == 10
    )

    change_row_history_registry.register(FilterRowHistoryStub())
    assert (
        len(
            RowHistoryHandler().list_row_history(
                database.workspace, table.id, row_id=999
            )
        )
        == 2
    )

    change_row_history_registry.unregister("row_history_op_stub")


@pytest.mark.django_db
@pytest.mark.row_history
def test_row_history_handler_delete_entries_older_than(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(
        name="Test", user=user, database=database
    )
    before_retention_period = datetime(2021, 1, 3, 23, 59, tzinfo=timezone.utc)
    after_retention_period = datetime(2021, 1, 4, 0, 1, tzinfo=timezone.utc)
    cutoff = datetime(2021, 1, 4, 0, 0, tzinfo=timezone.utc)
    common_params = {
        "table": table,
        "row_id": 999,
        "action_uuid": "uuid",
        "action_command_type": "cmd",
        "action_type": "type",
        "field_names": [],
        "fields_metadata": {},
        "before_values": {},
        "after_values": {},
    }
    entries = [
        RowHistory(**common_params, action_timestamp=before_retention_period),
        RowHistory(**common_params, action_timestamp=before_retention_period),
        RowHistory(**common_params, action_timestamp=before_retention_period),
        RowHistory(**common_params, action_timestamp=after_retention_period),
        RowHistory(**common_params, action_timestamp=after_retention_period),
    ]
    RowHistory.objects.bulk_create(entries)
    assert RowHistory.objects.count() == 5

    RowHistoryHandler().delete_entries_older_than(cutoff)

    assert RowHistory.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.row_history
def test_row_history_not_recorded_with_retention_zero_days(settings, data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(
        name="Test", user=user, database=database
    )
    name_field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )
    model = table.get_model()
    row = model.objects.create()

    # no history will be recorded with zero retention days
    settings.BASEROW_ROW_HISTORY_RETENTION_DAYS = 0
    UpdateRowsActionType.do(
        user,
        table,
        [
            {
                "id": row.id,
                f"field_{name_field.id}": "changed",
            }
        ],
        model,
    )

    assert RowHistory.objects.count() == 0

    # otherwise record row history
    settings.BASEROW_ROW_HISTORY_RETENTION_DAYS = 1
    UpdateRowsActionType.do(
        user,
        table,
        [
            {
                "id": row.id,
                f"field_{name_field.id}": "changed 2",
            }
        ],
        model,
    )

    assert RowHistory.objects.count() == 1

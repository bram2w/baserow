from unittest.mock import AsyncMock, patch

from django.db import transaction
from django.test.utils import override_settings

import pytest

from baserow.contrib.database.fields.dependencies.update_collector import (
    DependantRowsUpdate,
)
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.rows.signals import dependant_rows_updated
from baserow.contrib.database.ws.rows.signals import close_dependant_rows_broadcast
from baserow.contrib.database.ws.rows.tasks import broadcast_dependant_rows_updated


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_updating_a_row_broadcasts_dependant_rows_to_the_linked_table(
    mock_broadcast_task, data_fixture
):
    user = data_fixture.create_user()
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "b1"}])
        .created_rows[0]
    )
    row_a1 = (
        RowHandler()
        .create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])
        .created_rows[0]
    )
    mock_broadcast_task.reset_mock()

    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "renamed"}]
        )

    mock_broadcast_task.delay.assert_called_once_with(
        table_id=table_a.id,
        row_ids=[row_a1.id],
        updated_field_ids=[link_a_b.id],
        # A link row field display has no truthful before state to snapshot.
        serialized_rows_before=[],
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_updating_a_row_forwards_before_rows_for_formula_dependants(
    mock_broadcast_task, data_fixture
):
    user = data_fixture.create_user()
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific
    lookup_a = data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), '')"
    )

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "b1"}])
        .created_rows[0]
    )
    row_a1 = (
        RowHandler()
        .create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])
        .created_rows[0]
    )
    mock_broadcast_task.reset_mock()

    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "renamed"}]
        )

    serialized_rows_before = mock_broadcast_task.delay.call_args[1][
        "serialized_rows_before"
    ]
    assert [row["id"] for row in serialized_rows_before] == [row_a1.id]
    assert serialized_rows_before[0][lookup_a.db_column] == "b1"


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.table.signals.broadcast_to_permitted_users")
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_requires_refresh_sends_a_force_table_refresh(
    mock_broadcast_task, mock_broadcast_to_permitted_users, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    dependant_rows_updated.send(
        None,
        user=user,
        table=table,
        dependant_rows_updates=[
            DependantRowsUpdate(
                table=table, row_ids=[], field_ids=[1], requires_refresh=True
            )
        ],
        send_realtime_update=True,
    )

    mock_broadcast_task.delay.assert_not_called()
    mock_broadcast_to_permitted_users.delay.assert_called_once()
    payload = mock_broadcast_to_permitted_users.delay.call_args[0][4]
    assert payload["type"] == "table_updated"
    assert payload["force_table_refresh"] is True


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.table.signals.broadcast_to_permitted_users")
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_every_affected_table_under_the_limit_is_broadcast_exactly(
    mock_broadcast_task, mock_broadcast_to_permitted_users, data_fixture
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    tables = [data_fixture.create_database_table(database=database) for _ in range(12)]

    dependant_rows_updated.send(
        None,
        user=user,
        table=tables[0],
        dependant_rows_updates=[
            DependantRowsUpdate(
                table=table, row_ids=[1], field_ids=[1], requires_refresh=False
            )
            for table in tables
        ],
        send_realtime_update=True,
    )

    # A wide fan-out sends an invisible exact broadcast per table and never a
    # disruptive refresh; only the per-table row limit can force a refresh.
    assert mock_broadcast_task.delay.call_count == 12
    assert mock_broadcast_to_permitted_users.delay.call_count == 0


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.table.signals.broadcast_to_permitted_users")
@patch("baserow.contrib.database.ws.rows.signals.ViewRealtimeRowsHandler")
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_dependant_rows_updates_of_one_transaction_are_broadcast_once(
    mock_broadcast_task,
    mock_view_realtime_rows_handler,
    mock_broadcast_to_permitted_users,
    data_fixture,
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    broadcasts = []
    merged_updates = []
    handler = mock_view_realtime_rows_handler.return_value

    def get_visibility_changes(update):
        merged_updates.append(update)
        return [(f"view-{len(merged_updates)}", {"type": "rows_deleted"})]

    handler.get_dependant_rows_visibility_changes.side_effect = get_visibility_changes
    handler.broadcast_to_types.side_effect = lambda view, payload: broadcasts.append(
        ("visibility_changes", view)
    )
    mock_broadcast_task.delay.side_effect = lambda **kwargs: broadcasts.append(
        ("task", kwargs)
    )

    with transaction.atomic():
        for row_ids, value, visible_view_ids in (
            ([1], "first", {10}),
            ([1, 2], "second", set()),
        ):
            dependant_rows_updated.send(
                None,
                user=user,
                table=table,
                dependant_rows_updates=[
                    DependantRowsUpdate(
                        table=table,
                        row_ids=row_ids,
                        field_ids=[1],
                        requires_refresh=False,
                        before_rows={
                            row_id: {"id": row_id, "field_1": value}
                            for row_id in row_ids
                        },
                        before_visible_view_ids={
                            row_id: visible_view_ids for row_id in row_ids
                        },
                        before_checked_view_ids={10},
                    )
                ],
                send_realtime_update=True,
            )
        assert broadcasts == []

    # Decided again in the transaction after each cascade, from the first snapshot.
    assert len(merged_updates) == 2
    update = merged_updates[1]
    # Row 1's second snapshot shows the first update, which no client saw.
    assert update.before_rows == {
        1: {"id": 1, "field_1": "first"},
        2: {"id": 2, "field_1": "second"},
    }
    assert update.before_visible_view_ids == {1: {10}, 2: set()}
    assert update.before_checked_view_ids == {10}
    # Only the latest decision is sent, before the task is queued.
    assert broadcasts == [
        ("visibility_changes", "view-2"),
        (
            "task",
            dict(
                table_id=table.id,
                row_ids=[1, 2],
                updated_field_ids=[1],
                serialized_rows_before=[
                    {"id": 1, "field_1": "first"},
                    {"id": 2, "field_1": "second"},
                ],
            ),
        ),
    ]
    mock_broadcast_to_permitted_users.delay.assert_not_called()


@pytest.mark.django_db(transaction=True)
@override_settings(DEPENDANT_ROWS_REALTIME_UPDATE_LIMIT=2)
@patch("baserow.contrib.database.ws.table.signals.broadcast_to_permitted_users")
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_dependant_rows_updates_of_one_transaction_over_the_limit_refresh_once(
    mock_broadcast_task, mock_broadcast_to_permitted_users, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    with transaction.atomic():
        for row_ids in ([1, 2], [3]):
            dependant_rows_updated.send(
                None,
                user=user,
                table=table,
                dependant_rows_updates=[
                    DependantRowsUpdate(
                        table=table,
                        row_ids=row_ids,
                        field_ids=[1],
                        requires_refresh=False,
                    )
                ],
                send_realtime_update=True,
            )

    mock_broadcast_task.delay.assert_not_called()
    mock_broadcast_to_permitted_users.delay.assert_called_once()
    payload = mock_broadcast_to_permitted_users.delay.call_args[0][4]
    assert payload["force_table_refresh"] is True


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_dependant_rows_updates_of_a_rolled_back_savepoint_are_not_broadcast(
    mock_broadcast_task, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    def send(row_ids):
        dependant_rows_updated.send(
            None,
            user=user,
            table=table,
            dependant_rows_updates=[
                DependantRowsUpdate(
                    table=table, row_ids=row_ids, field_ids=[1], requires_refresh=False
                )
            ],
            send_realtime_update=True,
        )

    with transaction.atomic():
        try:
            with transaction.atomic():
                send([1])
                raise ValueError()
        except ValueError:
            pass
        send([2])

    mock_broadcast_task.delay.assert_called_once()
    assert mock_broadcast_task.delay.call_args[1]["row_ids"] == [2]


def _send_dependant_rows_update(user, table, row_ids):
    dependant_rows_updated.send(
        None,
        user=user,
        table=table,
        dependant_rows_updates=[
            DependantRowsUpdate(
                table=table, row_ids=row_ids, field_ids=[1], requires_refresh=False
            )
        ],
        send_realtime_update=True,
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_dependant_rows_updates_of_a_rolled_back_savepoint_after_others_are_dropped(
    mock_broadcast_task, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    with transaction.atomic():
        _send_dependant_rows_update(user, table, [1])
        try:
            with transaction.atomic():
                _send_dependant_rows_update(user, table, [2])
                raise ValueError()
        except ValueError:
            pass
        _send_dependant_rows_update(user, table, [3])

    assert [
        call.kwargs["row_ids"] for call in mock_broadcast_task.delay.call_args_list
    ] == [[1, 3]]


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_dependant_rows_updates_of_a_released_savepoint_are_broadcast_in_order(
    mock_broadcast_task, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    with transaction.atomic():
        _send_dependant_rows_update(user, table, [1])
        with transaction.atomic():
            _send_dependant_rows_update(user, table, [2])
        _send_dependant_rows_update(user, table, [3])

    assert [
        call.kwargs["row_ids"] for call in mock_broadcast_task.delay.call_args_list
    ] == [[1], [2, 3]]


@pytest.mark.parametrize(
    "closed_row_ids,broadcast_row_ids",
    [([1], [[1], [1, 2]]), ([5], [[1, 2]])],
    ids=["listed_row", "unlisted_row"],
)
@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_closing_a_dependant_rows_broadcast_on_a_listed_row_starts_a_new_one(
    mock_broadcast_task, data_fixture, closed_row_ids, broadcast_row_ids
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    with transaction.atomic():
        _send_dependant_rows_update(user, table, [1])
        close_dependant_rows_broadcast(table.id, closed_row_ids)
        _send_dependant_rows_update(user, table, [1, 2])

    assert [
        call.kwargs["row_ids"] for call in mock_broadcast_task.delay.call_args_list
    ] == broadcast_row_ids


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.rows.signals.ViewRealtimeRowsHandler")
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_visibility_changes_use_the_unknown_before_values_of_the_transaction(
    mock_broadcast_task, mock_view_realtime_rows_handler, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    handler = mock_view_realtime_rows_handler.return_value
    handler.get_dependant_rows_visibility_changes.return_value = []

    def send_update(row_ids, unknown_field_id):
        dependant_rows_updated.send(
            None,
            user=user,
            table=table,
            dependant_rows_updates=[
                DependantRowsUpdate(
                    table=table,
                    row_ids=row_ids,
                    field_ids=[unknown_field_id],
                    requires_refresh=False,
                    field_ids_with_unknown_before_values={unknown_field_id},
                )
            ],
            send_realtime_update=True,
        )

    with transaction.atomic():
        send_update([1], 10)
        close_dependant_rows_broadcast(table.id, [1])
        try:
            with transaction.atomic():
                send_update([2], 20)
                raise ValueError()
        except ValueError:
            pass
        send_update([3], 30)
        decided_update = handler.get_dependant_rows_visibility_changes.call_args.args[0]

    # The closed broadcast still counts, the rolled back savepoint doesn't.
    assert decided_update.row_ids == [3]
    assert decided_update.field_ids_with_unknown_before_values == {10, 30}


@pytest.mark.django_db(transaction=True)
@override_settings(DEPENDANT_ROWS_REALTIME_UPDATE_LIMIT=0)
@patch("baserow.contrib.database.ws.table.signals.broadcast_to_permitted_users")
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_nothing_is_sent_when_disabled(
    mock_broadcast_task, mock_broadcast_to_permitted_users, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    dependant_rows_updated.send(
        None,
        user=user,
        table=table,
        dependant_rows_updates=[
            DependantRowsUpdate(
                table=table, row_ids=[1], field_ids=[1], requires_refresh=False
            ),
            DependantRowsUpdate(
                table=table, row_ids=[], field_ids=[], requires_refresh=True
            ),
        ],
        send_realtime_update=True,
    )

    mock_broadcast_task.delay.assert_not_called()
    mock_broadcast_to_permitted_users.delay.assert_not_called()


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.table.signals.broadcast_to_permitted_users")
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
def test_nothing_is_sent_without_realtime_update(
    mock_broadcast_task, mock_broadcast_to_permitted_users, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    dependant_rows_updated.send(
        None,
        user=user,
        table=table,
        dependant_rows_updates=[
            DependantRowsUpdate(
                table=table, row_ids=[1], field_ids=[1], requires_refresh=False
            )
        ],
        send_realtime_update=False,
    )

    mock_broadcast_task.delay.assert_not_called()
    mock_broadcast_to_permitted_users.delay.assert_not_called()


@pytest.mark.django_db
@patch(
    "baserow.contrib.database.ws.rows.tasks.send_messages_to_channel_group",
    new_callable=AsyncMock,
)
def test_broadcast_task_sends_a_rows_updated_payload(mock_send, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    model = table.get_model()
    row_1 = model.objects.create(**{field.db_column: "a"})
    row_2 = model.objects.create(**{field.db_column: "b"})

    broadcast_dependant_rows_updated(
        table_id=table.id,
        row_ids=[row_1.id, row_2.id],
        updated_field_ids=[field.id],
    )

    mock_send.assert_called_once()
    message = mock_send.call_args[0][1]
    assert message.channel_group_name == f"table-{table.id}"
    payload = message.message["payload"]
    assert payload["type"] == "rows_updated"
    assert payload["table_id"] == table.id
    assert payload["updated_field_ids"] == [field.id]
    assert [row["id"] for row in payload["rows"]] == [row_1.id, row_2.id]
    assert payload["rows"][0][field.db_column] == "a"
    assert payload["rows_before_update"] == [{"id": row_1.id}, {"id": row_2.id}]
    assert message.message["ignore_web_socket_id"] is None


@pytest.mark.django_db
@patch(
    "baserow.contrib.database.ws.rows.tasks.send_messages_to_channel_group",
    new_callable=AsyncMock,
)
def test_broadcast_task_uses_provided_before_rows(mock_send, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    model = table.get_model()
    row_1 = model.objects.create(**{field.db_column: "a"})
    row_2 = model.objects.create(**{field.db_column: "b"})

    broadcast_dependant_rows_updated(
        table_id=table.id,
        row_ids=[row_1.id, row_2.id],
        updated_field_ids=[field.id],
        # Only row_1 has a snapshot; row_2 falls back to an id-only skeleton.
        serialized_rows_before=[{"id": row_1.id, field.db_column: "old"}],
    )

    payload = mock_send.call_args[0][1].message["payload"]
    assert payload["rows_before_update"] == [
        {"id": row_1.id, field.db_column: "old"},
        {"id": row_2.id},
    ]


@pytest.mark.django_db
@patch(
    "baserow.contrib.database.ws.rows.tasks.send_messages_to_channel_group",
    new_callable=AsyncMock,
)
def test_broadcast_task_skips_trashed_rows_and_missing_tables(mock_send, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    model = table.get_model()
    row_1 = model.objects.create(**{field.db_column: "a"})
    row_2 = model.objects.create(**{field.db_column: "b"}, trashed=True)

    broadcast_dependant_rows_updated(
        table_id=table.id, row_ids=[row_1.id, row_2.id], updated_field_ids=[field.id]
    )
    payload = mock_send.call_args[0][1].message["payload"]
    assert [row["id"] for row in payload["rows"]] == [row_1.id]

    mock_send.reset_mock()
    broadcast_dependant_rows_updated(
        table_id=table.id, row_ids=[row_2.id], updated_field_ids=[field.id]
    )
    mock_send.assert_not_called()

    broadcast_dependant_rows_updated(
        table_id=0, row_ids=[row_1.id], updated_field_ids=[field.id]
    )
    mock_send.assert_not_called()

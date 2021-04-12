import pytest

from unittest.mock import patch

from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_row_created(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    row = RowHandler().create_row(
        user=user, table=table, values={f"field_{field.id}": "Test"}
    )

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{table.id}"
    assert args[0][1]["type"] == "row_created"
    assert args[0][1]["table_id"] == table.id
    assert args[0][1]["row"]["id"] == row.id
    assert args[0][1]["before_row_id"] is None
    assert args[0][1]["row"][f"field_{field.id}"] == "Test"

    row_2 = RowHandler().create_row(
        user=user, table=table, before=row, values={f"field_{field.id}": "Test2"}
    )
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{table.id}"
    assert args[0][1]["type"] == "row_created"
    assert args[0][1]["table_id"] == table.id
    assert args[0][1]["row"]["id"] == row_2.id
    assert args[0][1]["before_row_id"] == row.id
    assert args[0][1]["row"][f"field_{field.id}"] == "Test2"


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_row_updated(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    field_2 = data_fixture.create_text_field(table=table)
    row = table.get_model().objects.create()
    RowHandler().update_row(
        user=user, table=table, row_id=row.id, values={f"field_{field.id}": "Test"}
    )

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{table.id}"
    assert args[0][1]["type"] == "row_updated"
    assert args[0][1]["table_id"] == table.id
    assert args[0][1]["row"]["id"] == row.id
    assert args[0][1]["row"][f"field_{field.id}"] == "Test"
    assert args[0][1]["row"][f"field_{field_2.id}"] is None

    row.refresh_from_db()
    setattr(row, f"field_{field_2.id}", "Second")
    row.save()
    RowHandler().update_row(
        user=user, table=table, row_id=row.id, values={f"field_{field.id}": "First"}
    )

    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{table.id}"
    assert args[0][1]["type"] == "row_updated"
    assert args[0][1]["table_id"] == table.id
    assert args[0][1]["row"]["id"] == row.id
    assert args[0][1]["row"][f"field_{field.id}"] == "First"
    assert args[0][1]["row"][f"field_{field_2.id}"] == "Second"


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_row_deleted(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    row = table.get_model().objects.create()
    row_id = row.id
    RowHandler().delete_row(user=user, table=table, row_id=row_id)

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{table.id}"
    assert args[0][1]["type"] == "row_deleted"
    assert args[0][1]["row_id"] == row_id
    assert args[0][1]["table_id"] == table.id

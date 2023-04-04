from unittest.mock import patch

import pytest

from baserow.contrib.database.table.handler import TableHandler
from baserow.core.utils import generate_hash


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.table.signals.broadcast_to_permitted_users")
def test_table_created(mock_broadcast_to_permitted_users, data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table, _ = TableHandler().create_table(user=user, database=database, name="Test")

    mock_broadcast_to_permitted_users.delay.assert_called_once()
    args = mock_broadcast_to_permitted_users.delay.call_args
    assert args[0][4]["type"] == "table_created"
    assert args[0][4]["table"]["id"] == table.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.table.signals.broadcast_to_permitted_users")
def test_table_updated(mock_broadcast_to_permitted_users, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    table = TableHandler().update_table(user=user, table=table, name="Test")

    mock_broadcast_to_permitted_users.delay.assert_called_once()
    args = mock_broadcast_to_permitted_users.delay.call_args
    assert args[0][4]["type"] == "table_updated"
    assert args[0][4]["table_id"] == table.id
    assert args[0][4]["table"]["id"] == table.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.table.signals.broadcast_to_group")
def test_tables_reordered(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)
    TableHandler().order_tables(user=user, database=database, order=[table.id])

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == table.database.workspace_id
    assert args[0][1]["type"] == "tables_reordered"
    assert args[0][1]["database_id"] == generate_hash(database.id)
    assert args[0][1]["order"] == [generate_hash(table.id)]


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.table.signals.broadcast_to_permitted_users")
def test_table_deleted(mock_broadcast_to_permitted_users, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    table_id = table.id
    database_id = table.database_id
    TableHandler().delete_table(user=user, table=table)

    mock_broadcast_to_permitted_users.delay.assert_called_once()
    args = mock_broadcast_to_permitted_users.delay.call_args
    assert args[0][4]["type"] == "table_deleted"
    assert args[0][4]["database_id"] == database_id
    assert args[0][4]["table_id"] == table_id

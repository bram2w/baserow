import pytest

from unittest.mock import patch

from baserow.contrib.database.fields.handler import FieldHandler


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_field_created(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = FieldHandler().create_field(
        user=user, table=table, type_name="text", name="Grid"
    )

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{table.id}"
    assert args[0][1]["type"] == "field_created"
    assert args[0][1]["field"]["id"] == field.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_field_updated(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    field = data_fixture.create_text_field(user=user)
    FieldHandler().update_field(user=user, field=field, name="field")

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{field.table.id}"
    assert args[0][1]["type"] == "field_updated"
    assert args[0][1]["field_id"] == field.id
    assert args[0][1]["field"]["id"] == field.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_field_deleted(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    field = data_fixture.create_text_field(user=user)
    field_id = field.id
    table_id = field.table_id
    FieldHandler().delete_field(user=user, field=field)

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{field.table.id}"
    assert args[0][1]["type"] == "field_deleted"
    assert args[0][1]["field_id"] == field_id
    assert args[0][1]["table_id"] == table_id

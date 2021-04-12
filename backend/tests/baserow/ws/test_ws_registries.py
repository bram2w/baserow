from unittest.mock import patch

from baserow.ws.registries import page_registry


@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_broadcast(mock_broadcast, data_fixture):
    table_page = page_registry.get("table")

    table_page.broadcast({"message": "test"}, table_id=1)
    mock_broadcast.delay.assert_called_once()
    args = mock_broadcast.delay.call_args
    assert args[0][0] == "table-1"
    assert args[0][1]["message"] == "test"
    assert args[0][2] is None

    table_page.broadcast({"message": "test2"}, ignore_web_socket_id="123", table_id=2)
    args = mock_broadcast.delay.call_args
    assert args[0][0] == "table-2"
    assert args[0][1]["message"] == "test2"
    assert args[0][2] == "123"

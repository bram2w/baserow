import pytest
import uuid

from unittest.mock import patch

from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.webhooks.registries.call_webhook")
def test_signal_listener(mock_call_webhook, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    webhook = data_fixture.create_table_webhook(
        user=user,
        table=table,
        url="http://localhost/",
        include_all_events=False,
        events=["row.created"],
        headers={"Baserow-header-1": "Value 1"},
    )

    RowHandler().create_row(user=user, table=table, values={})
    mock_call_webhook.delay.assert_called_once()
    args, kwargs = mock_call_webhook.delay.call_args
    assert kwargs["webhook_id"] == webhook.id
    assert isinstance(kwargs["event_id"], uuid.UUID)
    assert kwargs["event_type"] == "row.created"
    assert kwargs["headers"]["Baserow-header-1"] == "Value 1"
    assert kwargs["headers"]["Content-type"] == "application/json"
    assert kwargs["headers"]["X-Baserow-Event"] == "row.created"
    assert len(kwargs["headers"]["X-Baserow-Delivery"]) > 1
    assert kwargs["method"] == "POST"
    assert kwargs["url"] == "http://localhost/"
    assert kwargs["payload"] == {
        "table_id": table.id,
        "event_id": kwargs["payload"]["event_id"],
        "event_type": "row.created",
        "row_id": 1,
        "values": {"id": 1, "order": "1.00000000000000000000"},
    }

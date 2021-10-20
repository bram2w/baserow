from unittest.mock import patch

import pytest
from freezegun import freeze_time
from django.test.utils import override_settings

from baserow_premium.row_comments.handler import RowCommentHandler


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_row_comment_created(mock_broadcast_to_channel_group, premium_data_fixture):
    user = premium_data_fixture.create_user(
        first_name="test_user", has_active_premium_license=True
    )
    table, fields, rows = premium_data_fixture.build_table(
        columns=[("text", "text")], rows=["first row"], user=user
    )

    with freeze_time("2020-01-02 12:00"):
        c = RowCommentHandler.create_comment(user, table.id, rows[0].id, "comment")

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args

    assert args[0][0] == f"table-{table.id}"
    assert args[0][1]["type"] == "row_comment_created"
    assert args[0][1]["row_comment"] == {
        "comment": "comment",
        "created_on": "2020-01-02T12:00:00Z",
        "first_name": "test_user",
        "id": c.id,
        "user_id": user.id,
        "row_id": rows[0].id,
        "table_id": table.id,
        "updated_on": "2020-01-02T12:00:00Z",
    }

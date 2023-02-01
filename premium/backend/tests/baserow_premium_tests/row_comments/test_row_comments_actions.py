from django.test.utils import override_settings

import pytest
from baserow_premium.row_comments.actions import CreateRowCommentActionType

from baserow.core.action.registries import action_type_registry


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_db_token_action_type(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    table = premium_data_fixture.create_database_table(user=user)
    premium_data_fixture.create_text_field(table=table)
    rows = premium_data_fixture.create_rows_in_table(table, [[]])

    row_comment = action_type_registry.get(CreateRowCommentActionType.type).do(
        user, table.id, rows[0].id, "comment"
    )
    assert row_comment.comment == "comment"

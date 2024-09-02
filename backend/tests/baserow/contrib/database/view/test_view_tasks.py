from unittest.mock import patch

import pytest

from baserow.contrib.database.views.tasks import update_view_index
from baserow.test_utils.helpers import independent_test_db_connection


@pytest.mark.django_db
def test_update_view_index_ignore_missing_view():
    # no exception occurs
    update_view_index(999)


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.views.tasks._set_pending_view_index_update")
def test_update_view_index_is_rescheduled_if_cannot_take_lock(
    mock_set_pending_view_index_update, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    view = data_fixture.create_grid_view(table=table)

    update_view_index(view.id)

    assert mock_set_pending_view_index_update.call_count == 0

    with independent_test_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"LOCK TABLE {table.get_database_table_name()} IN ROW EXCLUSIVE MODE"
            )

        update_view_index(view.id)

    assert mock_set_pending_view_index_update.call_count == 1

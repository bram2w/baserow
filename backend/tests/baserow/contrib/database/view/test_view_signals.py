from unittest.mock import patch

import pytest

from baserow.contrib.database.views.signals import (
    view_loaded_create_indexes_and_columns,
)


@patch("baserow.contrib.database.views.handler.ViewIndexingHandler")
@pytest.mark.django_db
def test_view_loaded_creates_last_modified_by_column(indexing_handler, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(
        user=user, last_modified_by_column_added=True
    )
    table_model = table.get_model()
    view = data_fixture.create_grid_view(user=user, table=table)

    # won't schedule column creation if already added
    with patch(
        "baserow.contrib.database.table.tasks.setup_created_by_and_last_modified_by_column"
    ) as setup:
        view_loaded_create_indexes_and_columns(
            None, view, table_model, table=table, user=user
        )
        setup.delay.assert_not_called()

    # schedule column creation if not added yet
    table.last_modified_by_column_added = False
    table.save()
    with patch(
        "baserow.contrib.database.table.tasks.setup_created_by_and_last_modified_by_column"
    ) as setup:
        view_loaded_create_indexes_and_columns(
            None, view, table_model, table=table, user=user
        )
        setup.delay.assert_called_once_with(table_id=view.table.id)

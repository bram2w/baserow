from typing import List, Optional

from django.conf import settings

from loguru import logger

from baserow.config.celery import app
from baserow.contrib.database.search.exceptions import (
    PostgresFullTextSearchDisabledException,
)


@app.task(
    queue="export",
    time_limit=settings.CELERY_SEARCH_UPDATE_HARD_TIME_LIMIT,
)
def async_update_tsvector_columns(
    table_id: int,
    update_tsvs_for_changed_rows_only: bool,
    field_ids_to_restrict_update_to: Optional[List[int]] = None,
):
    """
    Responsible for asynchronously updating the `tsvector` columns on a table.

    :param table_id: The ID of the table we'd like to update the tsvectors for.
    :param update_tsvs_for_changed_rows_only: By default we will only update rows on
        the table which have changed since the last search update.
        If set to `False`, we will index all cells that match the other parameters.
    :param field_ids_to_restrict_update_to: If provided only the fields matching the
        provided ids will have their tsv columns updated.
    """

    from baserow.contrib.database.search.handler import SearchHandler
    from baserow.contrib.database.table.handler import TableHandler

    table = TableHandler().get_table(table_id)
    try:
        SearchHandler.update_tsvector_columns_locked(
            table, update_tsvs_for_changed_rows_only, field_ids_to_restrict_update_to
        )
    except PostgresFullTextSearchDisabledException:
        logger.debug(f"Postgres full-text search is disabled.")

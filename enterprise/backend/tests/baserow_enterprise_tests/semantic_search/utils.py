import time

from django.db import connection

import pytest

from baserow_enterprise.semantic_search.handler import SemanticSearchHandler
from baserow_enterprise.semantic_search.vector_table import SemanticSearchVectorTable

# Search data updates are deferred in tests by default, but they're how changed
# cells reach the semantic search index.
enable_search_data_updates = pytest.mark.enable_signals(
    "baserow.contrib.database.search.tasks.schedule_update_search_data.delay"
)


def get_chunk_counts(field) -> dict[int, int]:
    """Returns the number of chunks per row of the field."""

    vector_table = SemanticSearchVectorTable(field.table.database.workspace_id)
    if not vector_table.exists():
        return {}
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT row_id, count(*) FROM {vector_table.name} "  # noqa: S608
            "WHERE field_id = %s GROUP BY row_id",
            [field.id],
        )
        return dict(cursor.fetchall())


def index(table, seconds: float = 60) -> bool:
    return SemanticSearchHandler().index_table(table, time.monotonic() + seconds)

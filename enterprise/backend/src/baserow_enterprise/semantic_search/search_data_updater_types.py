from datetime import datetime
from itertools import groupby
from typing import Optional

from django.conf import settings
from django.db.models import QuerySet

from loguru import logger

from baserow.contrib.database.search.registries import SearchDataUpdaterType
from baserow.contrib.database.table.models import Table
from baserow.core.embeddings import EmbeddingsServiceError

from .handler import INDEX_BATCH_ROWS, SemanticSearchHandler, _FieldIndexer
from .models import SemanticSearchField, SemanticSearchPendingUpdate
from .vector_table import SemanticSearchVectorTable

UPDATE_THROTTLE_SECONDS = 5


class SemanticSearchDataUpdaterType(SearchDataUpdaterType):
    type = "semantic_search"
    queue_model = SemanticSearchPendingUpdate
    reschedule_flag_key_prefix = "semantic_search_data_lock"
    row_batch_size = INDEX_BATCH_ROWS
    full_field_updates_cover_row_updates = False

    def get_update_task(self):
        from .tasks import update_semantic_search_data

        return update_semantic_search_data

    def get_throttle_seconds(self) -> int:
        return UPDATE_THROTTLE_SECONDS

    def get_time_budget_seconds(self) -> int:
        return settings.BASEROW_SEMANTIC_SEARCH_TASK_TIME_BUDGET_SECONDS

    def _get_semantic_search_fields(
        self, table: Table, field_ids: list[int] | None
    ) -> QuerySet:
        semantic_search_fields = SemanticSearchField.objects.filter(
            field__table=table, field__trashed=False
        )
        if field_ids is not None:
            semantic_search_fields = semantic_search_fields.filter(
                field_id__in=field_ids
            )
        return semantic_search_fields

    def get_queued_field_ids(
        self, table: Table, field_ids: list[int] | None
    ) -> list[int]:
        return list(
            self._get_semantic_search_fields(table, field_ids).values_list(
                "field_id", flat=True
            )
        )

    def queue(
        self,
        table: Table,
        field_ids: list[int] | None = None,
        row_ids: list[int] | None = None,
    ) -> bool:
        handler = SemanticSearchHandler()
        if row_ids is not None and handler.can_index(table.database.workspace):
            # A few changed rows don't make the field show that it's being indexed.
            return super().queue(table, field_ids, row_ids)

        # While indexing is paused, one update of all rows replaces any number of
        # changed rows, and it's cheap because unchanged values are skipped.
        semantic_search_fields = list(
            self._get_semantic_search_fields(table, field_ids)
        )
        if not semantic_search_fields:
            return False
        handler.queue_full_updates(table, semantic_search_fields, start_indexing=False)
        return True

    def prepare(self, table: Table) -> bool:
        handler = SemanticSearchHandler()
        workspace = table.database.workspace
        if (
            workspace is None
            or not handler.can_index(workspace)
            or handler.is_retry_postponed(table)
        ):
            return False
        SemanticSearchVectorTable(workspace.id).create_if_not_exists()
        return True

    def _get_indexer(
        self, table: Table, field_id: int, deadline: Optional[float]
    ) -> Optional[_FieldIndexer]:
        """
        :param table: The table of the field.
        :param field_id: The field that's indexed.
        :param deadline: The `time.monotonic()` after which no new batch is started.
        :return: None if the field can't be indexed anymore, for example because
            semantic search was disabled or the field was trashed. It's indexed
            again when it's restored.
        """

        handler = SemanticSearchHandler()
        semantic_search_field = (
            self._get_semantic_search_fields(table, [field_id])
            .select_related("field")
            .first()
        )
        if semantic_search_field is None:
            return None
        field = semantic_search_field.field.specific
        semantic_search_field_type = handler.get_semantic_search_field_type(field)
        if semantic_search_field_type is None:
            return None
        return _FieldIndexer(
            field,
            semantic_search_field_type,
            table.get_model(),
            SemanticSearchVectorTable(table.database.workspace_id),
            deadline,
        )

    def process_full_field_updates(
        self,
        table: Table,
        updates: list[SemanticSearchPendingUpdate],
        check_timestamp: datetime,
        deadline: Optional[float],
    ) -> bool:
        for update in updates:
            indexer = self._get_indexer(table, update.field_id, deadline)
            if indexer is not None and not indexer.index_all_rows(
                update, check_timestamp
            ):
                return False
        return True

    def process_row_updates(
        self,
        table: Table,
        updates: list[SemanticSearchPendingUpdate],
        deadline: Optional[float],
    ) -> int:
        processed = 0
        for field_id, field_updates in groupby(updates, lambda update: update.field_id):
            row_ids = [update.row_id for update in field_updates]
            indexer = self._get_indexer(table, field_id, deadline)
            indexed = len(row_ids) if indexer is None else indexer.index_rows(row_ids)
            processed += indexed
            if indexed < len(row_ids):
                break
        return processed

    def process_pending_updates(
        self, table: Table, deadline: Optional[float] = None
    ) -> bool:
        handler = SemanticSearchHandler()
        try:
            completed = super().process_pending_updates(table, deadline)
        finally:
            handler.mark_indexed(table)
        handler.clear_indexing_failures(table)
        return completed

    def get_retry_countdown(self, table: Table, exception: Exception) -> int | None:
        if not isinstance(exception, EmbeddingsServiceError):
            return None
        countdown = SemanticSearchHandler().mark_indexing_failed(table)
        logger.warning(
            "Semantic search indexing of table {} failed, retrying in {}s.",
            table.id,
            countdown,
        )
        return countdown

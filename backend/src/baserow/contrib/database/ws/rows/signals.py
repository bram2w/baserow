from typing import Any, Dict, List, Optional

from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from baserow.contrib.database.rows import signals as row_signals
from baserow.contrib.database.rows.registries import row_metadata_registry
from baserow.contrib.database.table.models import GeneratedTableModel
from baserow.ws.registries import page_registry


@receiver(row_signals.rows_created)
def rows_created(sender, rows, before, user, table, model, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            RealtimeRowMessages.rows_created(
                table_id=table.id,
                serialized_rows=get_row_serializer_class(
                    model, RowSerializer, is_response=True
                )(rows, many=True).data,
                metadata=row_metadata_registry.generate_and_merge_metadata_for_rows(
                    table, [row.id for row in rows]
                ),
                before=before,
            ),
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )


@receiver(row_signals.before_rows_update)
def before_rows_update(sender, rows, user, table, model, updated_field_ids, **kwargs):
    return get_row_serializer_class(model, RowSerializer, is_response=True)(
        rows, many=True
    ).data


@receiver(row_signals.rows_updated)
def rows_updated(
    sender, rows, user, table, model, before_return, updated_field_ids, **kwargs
):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            RealtimeRowMessages.rows_updated(
                table_id=table.id,
                serialized_rows_before_update=dict(before_return)[before_rows_update],
                serialized_rows=get_row_serializer_class(
                    model, RowSerializer, is_response=True
                )(rows, many=True).data,
                metadata=row_metadata_registry.generate_and_merge_metadata_for_rows(
                    table, [row.id for row in rows]
                ),
            ),
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )


@receiver(row_signals.before_rows_delete)
def before_rows_delete(sender, rows, user, table, model, **kwargs):
    return get_row_serializer_class(model, RowSerializer, is_response=True)(
        rows, many=True
    ).data


@receiver(row_signals.rows_deleted)
def rows_deleted(sender, rows, user, table, model, before_return, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            RealtimeRowMessages.rows_deleted(
                table_id=table.id,
                serialized_rows=dict(before_return)[before_rows_delete],
            ),
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )


@receiver(row_signals.row_orders_recalculated)
def row_orders_recalculated(sender, table, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            RealtimeRowMessages.row_orders_recalculated(table_id=table.id),
            table_id=table.id,
        )
    )


class RealtimeRowMessages:
    """
    A collection of functions which construct the payloads for the realtime
    websocket messages related to rows.
    """

    @staticmethod
    def rows_deleted(
        table_id: int, serialized_rows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return {
            "type": "rows_deleted",
            "table_id": table_id,
            "row_ids": [r["id"] for r in serialized_rows],
            "rows": serialized_rows,
        }

    @staticmethod
    def rows_created(
        table_id: int,
        serialized_rows: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        before: Optional[GeneratedTableModel],
    ) -> Dict[str, Any]:
        return {
            "type": "rows_created",
            "table_id": table_id,
            "rows": serialized_rows,
            "metadata": metadata,
            "before_row_id": before.id if before else None,
        }

    @staticmethod
    def rows_updated(
        table_id: int,
        serialized_rows_before_update: List[Dict[str, Any]],
        serialized_rows: List[Dict[str, Any]],
        metadata: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "type": "rows_updated",
            "table_id": table_id,
            # The web-frontend expects a serialized version of the rows before it
            # was updated in order to estimate what position the row had in the
            # view.
            "rows_before_update": serialized_rows_before_update,
            "rows": serialized_rows,
            "metadata": metadata,
        }

    @staticmethod
    def row_orders_recalculated(table_id: int) -> Dict[str, Any]:
        return {
            "type": "row_orders_recalculated",
            "table_id": table_id,
        }

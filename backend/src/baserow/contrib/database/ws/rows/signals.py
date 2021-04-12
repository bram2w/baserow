from django.dispatch import receiver
from django.db import transaction

from baserow.ws.registries import page_registry

from baserow.contrib.database.rows import signals as row_signals
from baserow.contrib.database.api.rows.serializers import (
    get_row_serializer_class,
    RowSerializer,
)


@receiver(row_signals.row_created)
def row_created(sender, row, before, user, table, model, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {
                "type": "row_created",
                "table_id": table.id,
                "row": get_row_serializer_class(model, RowSerializer, is_response=True)(
                    row
                ).data,
                "before_row_id": before.id if before else None,
            },
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )


@receiver(row_signals.row_updated)
def row_updated(sender, row, user, table, model, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {
                "type": "row_updated",
                "table_id": table.id,
                "row": get_row_serializer_class(model, RowSerializer, is_response=True)(
                    row
                ).data,
            },
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )


@receiver(row_signals.row_deleted)
def row_deleted(sender, row_id, row, user, table, model, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {"type": "row_deleted", "table_id": table.id, "row_id": row_id},
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )

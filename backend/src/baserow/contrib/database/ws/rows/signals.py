from django.dispatch import receiver
from django.db import transaction

from baserow.contrib.database.rows.registries import row_metadata_registry
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
                "metadata": row_metadata_registry.generate_and_merge_metadata_for_row(
                    table, row.id
                ),
                "before_row_id": before.id if before else None,
            },
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )


@receiver(row_signals.before_row_update)
def before_row_update(sender, row, user, table, model, **kwargs):
    # Generate a serialized version of the row before it is updated. The
    # `row_updated` receiver needs this serialized version because it can't serialize
    # the old row after it has been updated.
    return get_row_serializer_class(model, RowSerializer, is_response=True)(row).data


@receiver(row_signals.row_updated)
def row_updated(sender, row, user, table, model, before_return, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {
                "type": "row_updated",
                "table_id": table.id,
                # The web-frontend expects a serialized version of the row before it
                # was updated in order the estimate what position the row had in the
                # view.
                "row_before_update": dict(before_return)[before_row_update],
                "row": get_row_serializer_class(model, RowSerializer, is_response=True)(
                    row
                ).data,
                "metadata": row_metadata_registry.generate_and_merge_metadata_for_row(
                    table, row.id
                ),
            },
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )


@receiver(row_signals.before_row_delete)
def before_row_delete(sender, row, user, table, model, **kwargs):
    # Generate a serialized version of the row before it is deleted. The
    # `row_deleted` receiver needs this serialized version because it can't serialize
    # the row after is has been deleted.
    return get_row_serializer_class(model, RowSerializer, is_response=True)(row).data


@receiver(row_signals.row_deleted)
def row_deleted(sender, row_id, row, user, table, model, before_return, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {
                "type": "row_deleted",
                "table_id": table.id,
                "row_id": row_id,
                # The web-frontend expects a serialized version of the row that is
                # deleted in order the estimate what position the row had in the view.
                "row": dict(before_return)[before_row_delete],
            },
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )

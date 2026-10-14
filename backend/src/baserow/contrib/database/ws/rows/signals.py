import dataclasses
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Set, Tuple

from django.conf import settings
from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.database.api.rows.serializers import (
    RowHistorySerializer,
    RowSerializer,
    get_row_serializer_class,
    serialize_rows_for_response,
)
from baserow.contrib.database.fields.dependencies.update_collector import (
    DependantRowsUpdate,
    merge_dependant_rows_updates,
)
from baserow.contrib.database.rows import signals as row_signals
from baserow.contrib.database.rows.registries import row_metadata_registry
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.table.signals import table_updated
from baserow.contrib.database.views.models import View
from baserow.contrib.database.ws.rows.messages import RealtimeRowMessages
from baserow.contrib.database.ws.rows.tasks import broadcast_dependant_rows_updated
from baserow.contrib.database.ws.views.rows.handler import ViewRealtimeRowsHandler
from baserow.ws.registries import PageType, page_registry

if TYPE_CHECKING:
    from baserow.contrib.database.rows.models import RowHistory


@receiver(row_signals.before_rows_update)
def serialize_rows_values(
    sender,
    rows,
    user,
    table,
    model,
    updated_field_ids,
    serialize_only_updated_fields: bool = False,
    **kwargs,
):
    return serialize_rows_for_response(
        rows,
        model,
        field_ids=updated_field_ids if serialize_only_updated_fields else None,
    )


@receiver(row_signals.rows_created)
def rows_created(
    sender,
    rows,
    before,
    user,
    table,
    model,
    send_realtime_update=True,
    send_webhook_events=True,
    **kwargs,
):
    if not send_realtime_update:
        return

    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            RealtimeRowMessages.rows_created(
                table_id=table.id,
                serialized_rows=get_row_serializer_class(
                    model, RowSerializer, is_response=True
                )(rows, many=True).data,
                metadata=row_metadata_registry.generate_and_merge_metadata_for_rows(
                    user, table, [row.id for row in rows]
                ),
                before=before,
            ),
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )


@receiver(row_signals.rows_updated)
def rows_updated(
    sender,
    rows,
    user,
    table,
    model,
    before_return,
    updated_field_ids,
    send_realtime_update=True,
    serialize_only_updated_fields: bool = False,
    **kwargs,
):
    if not send_realtime_update:
        return

    table_page_type = page_registry.get("table")
    before_rows_values = dict(before_return)[serialize_rows_values]
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            RealtimeRowMessages.rows_updated(
                table_id=table.id,
                serialized_rows_before_update=before_rows_values,
                serialized_rows=get_row_serializer_class(
                    model,
                    RowSerializer,
                    is_response=True,
                    # in some cases the caller may want to serialize just the fields
                    # that were provided in updated_field_ids list (i.e. field rules).
                    # Otherwise, we need to serialize all fields (i.e. in webhooks).
                    field_ids=updated_field_ids
                    if serialize_only_updated_fields
                    else None,
                )(rows, many=True).data,
                # Broadcast a list of updated fields so that the listener can take
                # action even if the value didn't change.
                updated_field_ids=list(updated_field_ids),
                metadata=row_metadata_registry.generate_and_merge_metadata_for_rows(
                    user, table, [row.id for row in rows]
                ),
            ),
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )


class DependantRowsBroadcast:
    """
    The dependency cascades into a table during a transaction, broadcast as one
    update once it commits, so a row's before state is the one before the
    transaction and never one in between that no client received. The rows
    leaving or entering a view are decided after every cascade, while the
    cascades still lock them.
    """

    def __init__(self, sender: Any, table: Table) -> None:
        """
        :param sender: The sender of the first dependant rows updated signal.
        :param table: The table the cascades changed rows of.
        """

        self.sender = sender
        self.table = table
        self.updates: List[DependantRowsUpdate] = []
        self.visibility_changes: List[Tuple[View, Dict[str, Any]]] = []
        self.closed = False
        self.savepoint_ids: Set[str] = set(transaction.get_connection().savepoint_ids)

    def is_joinable(self) -> bool:
        """
        :return: Whether a cascade at this point of the transaction can join it:
            not once it's closed, nor in a savepoint opened after it, which could
            roll back the cascade but not the broadcast.
        """

        return not self.closed and (
            set(transaction.get_connection().savepoint_ids) <= self.savepoint_ids
        )

    def add(self, update: DependantRowsUpdate) -> None:
        """
        Adds a cascade update of the table and decides again which rows left or
        entered a view since the first cascade.

        :param update: The cascade update of the table.
        :return: None, the outcome is recorded in `visibility_changes`.
        """

        self.updates.append(update)
        merged_update = self.get_merged_update()
        self.visibility_changes = (
            []
            if merged_update is None or merged_update.requires_refresh
            else ViewRealtimeRowsHandler().get_dependant_rows_visibility_changes(
                dataclasses.replace(
                    merged_update,
                    field_ids_with_unknown_before_values=(
                        self.get_transaction_field_ids_with_unknown_before_values()
                    ),
                )
            )
        )

    def get_transaction_field_ids_with_unknown_before_values(self) -> Set[int]:
        """
        :return: The ids of the table's fields whose before values any cascade
            of the transaction so far left unknown, the closed broadcasts
            included. A rolled back savepoint drops its broadcasts, so its
            cascades are left out.
        """

        return {
            field_id
            for broadcast in [self, *_get_dependant_rows_broadcasts(self.table.id)]
            for update in broadcast.updates
            for field_id in update.field_ids_with_unknown_before_values
        }

    def get_merged_update(self) -> Optional[DependantRowsUpdate]:
        """
        :return: The cascade updates of the table merged into one, or None when
            they changed no row.
        """

        merged_updates = merge_dependant_rows_updates(self.updates)
        return merged_updates[0] if merged_updates else None

    def lists_any_row(self, row_ids: Iterable[int]) -> bool:
        """
        :param row_ids: The ids of rows of the table.
        :return: Whether a cascade update listed any of the rows.
        """

        row_ids = set(row_ids)
        return any(row_ids.intersection(update.row_ids) for update in self.updates)

    def __call__(self) -> None:
        """
        Broadcasts the merged update once the transaction committed, or refreshes
        the whole table when it changed too many rows. The rows entering or
        leaving a view are broadcast first, because the task broadcasting the new
        values can run after later commits.

        :return: None.
        """

        update = self.get_merged_update()
        if update is None:
            return
        handler = ViewRealtimeRowsHandler()
        if update.requires_refresh:
            table_updated.send(
                self.sender, table=self.table, user=None, force_table_refresh=True
            )
            handler.broadcast_force_rows_refresh_to_views(self.table)
            return
        for view, payload in self.visibility_changes:
            handler.broadcast_to_types(view, payload)
        broadcast_dependant_rows_updated.delay(
            table_id=update.table.id,
            row_ids=list(update.row_ids),
            updated_field_ids=list(update.field_ids),
            serialized_rows_before=list(update.before_rows.values()),
        )


def _get_dependant_rows_broadcasts(table_id: int) -> List[DependantRowsBroadcast]:
    """
    :param table_id: The id of the table.
    :return: The broadcasts of the cascades into the table registered in the
        current transaction, in order.
    """

    return [
        callback
        for _, callback, _ in transaction.get_connection().run_on_commit
        if isinstance(callback, DependantRowsBroadcast)
        and callback.table.id == table_id
    ]


def _get_latest_dependant_rows_broadcast(
    table_id: int,
) -> Optional[DependantRowsBroadcast]:
    """
    :param table_id: The id of the table.
    :return: The latest broadcast of the cascades into the table in the current
        transaction, if any.
    """

    broadcasts = _get_dependant_rows_broadcasts(table_id)
    return broadcasts[-1] if broadcasts else None


def close_dependant_rows_broadcast(table_id: int, row_ids: Iterable[int]) -> None:
    """
    Makes the next cascades into the table start a new broadcast when the
    current one listed any of the rows, because the row signals just told the
    views that those rows left or entered them: merging a later cascade across
    that change would tell them again.

    :param table_id: The id of the table the rows belong to.
    :param row_ids: The ids of the rows that left or entered a view.
    :return: None.
    """

    broadcast = _get_latest_dependant_rows_broadcast(table_id)
    if broadcast is not None and broadcast.lists_any_row(row_ids):
        broadcast.closed = True


@receiver(row_signals.dependant_rows_updated)
def dependant_rows_updated(
    sender,
    user,
    table,
    dependant_rows_updates: List[DependantRowsUpdate],
    send_realtime_update: bool = True,
    **kwargs,
):
    """
    Broadcasts realtime events for rows changed by a dependency cascade so the
    affected tables' subscribers see the new values without refreshing. Tables
    with more affected rows than the limit receive a whole-table refresh instead.
    """

    if not send_realtime_update or not dependant_rows_updates:
        return
    if settings.DEPENDANT_ROWS_REALTIME_UPDATE_LIMIT <= 0:
        return

    for update in dependant_rows_updates:
        broadcast = _get_latest_dependant_rows_broadcast(update.table.id)
        if broadcast is not None and broadcast.is_joinable():
            broadcast.add(update)
        else:
            broadcast = DependantRowsBroadcast(sender, update.table)
            broadcast.add(update)
            transaction.on_commit(broadcast)


@receiver(row_signals.rows_ai_values_generation_error)
def rows_ai_values_generation_error(
    sender, user, rows, field, table, error_message, **kwargs
):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {
                "type": "rows_ai_values_generation_error",
                "field_id": field.id,
                "table_id": table.id,
                "row_ids": [row.id for row in rows],
                "error": error_message,
            },
            None,
            table_id=table.id,
        )
    )


@receiver(row_signals.before_rows_delete)
def before_rows_delete(sender, rows, user, table, model, **kwargs):
    return get_row_serializer_class(model, RowSerializer, is_response=True)(
        rows, many=True
    ).data


@receiver(row_signals.rows_deleted)
def rows_deleted(
    sender, rows, user, table, model, before_return, send_realtime_update=True, **kwargs
):
    if not send_realtime_update:
        return

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


@receiver(row_signals.rows_history_updated)
def rows_history_updated(
    sender,
    table_id,
    row_history_entries: "list[RowHistory]",
    **kwargs,
):
    row_page_type: PageType = page_registry.get("row")

    def send_rows():
        payloads_with_group_kws = [
            (
                {
                    "table_id": table_id,
                    "row_id": entry.row_id,
                },
                {
                    "type": "row_history_updated",
                    "row_history_entry": RowHistorySerializer(entry).data,
                    "table_id": table_id,
                    "row_id": entry.row_id,
                },
            )
            for entry in row_history_entries
        ]
        row_page_type.broadcast_many(
            payloads_with_group_kws,
            table_id=table_id,
        )

    transaction.on_commit(send_rows)

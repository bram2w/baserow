from typing import Optional, Any, Dict, Iterable

from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.api.rows.serializers import (
    get_row_serializer_class,
    RowSerializer,
)
from baserow.contrib.database.rows import signals as row_signals
from baserow.contrib.database.table.models import GeneratedTableModel
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View
from baserow.contrib.database.views.registries import view_type_registry
from baserow.contrib.database.ws.rows.signals import RealtimeRowMessages
from baserow.ws.registries import page_registry


def _serialize_row(model, row):
    return get_row_serializer_class(model, RowSerializer, is_response=True)(row).data


def _send_row_created_event_to_views(
    serialized_row: Dict[Any, Any],
    before: Optional[GeneratedTableModel],
    public_views: Iterable[View],
):
    view_page_type = page_registry.get("view")
    handler = ViewHandler()
    for public_view in public_views:
        view_type = view_type_registry.get_by_model(public_view.specific_class)
        if not view_type.when_shared_publicly_requires_realtime_events:
            continue

        restricted_serialized_row = handler.restrict_row_for_view(
            public_view, serialized_row
        )
        view_page_type.broadcast(
            RealtimeRowMessages.row_created(
                table_id=PUBLIC_PLACEHOLDER_ENTITY_ID,
                serialized_row=restricted_serialized_row,
                metadata={},
                before=before,
            ),
            slug=public_view.slug,
        )


def _send_row_deleted_event_to_views(
    serialized_deleted_row: Dict[Any, Any], public_views: Iterable[View]
):
    view_page_type = page_registry.get("view")
    handler = ViewHandler()
    for public_view in public_views:
        view_type = view_type_registry.get_by_model(public_view.specific_class)
        if not view_type.when_shared_publicly_requires_realtime_events:
            continue

        restricted_serialized_deleted_row = handler.restrict_row_for_view(
            public_view, serialized_deleted_row
        )
        view_page_type.broadcast(
            RealtimeRowMessages.row_deleted(
                table_id=PUBLIC_PLACEHOLDER_ENTITY_ID,
                serialized_row=restricted_serialized_deleted_row,
            ),
            slug=public_view.slug,
        )


@receiver(row_signals.row_created)
def public_row_created(sender, row, before, user, table, model, **kwargs):
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    transaction.on_commit(
        lambda: _send_row_created_event_to_views(
            _serialize_row(model, row),
            before,
            row_checker.get_public_views_where_row_is_visible(row),
        ),
    )


@receiver(row_signals.before_row_delete)
def public_before_row_delete(sender, row, user, table, model, **kwargs):
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    return {
        "deleted_row_public_views": (
            row_checker.get_public_views_where_row_is_visible(row)
        ),
        "deleted_row": _serialize_row(model, row),
    }


@receiver(row_signals.row_deleted)
def public_row_deleted(
    sender, row_id, row, user, table, model, before_return, **kwargs
):
    public_views = dict(before_return)[public_before_row_delete][
        "deleted_row_public_views"
    ]
    serialized_deleted_row = dict(before_return)[public_before_row_delete][
        "deleted_row"
    ]
    transaction.on_commit(
        lambda: _send_row_deleted_event_to_views(serialized_deleted_row, public_views)
    )


@receiver(row_signals.before_row_update)
def public_before_row_update(
    sender, row, user, table, model, updated_field_ids, **kwargs
):
    # Generate a serialized version of the row before it is updated. The
    # `row_updated` receiver needs this serialized version because it can't serialize
    # the old row after it has been updated.
    row_checker = ViewHandler().get_public_views_row_checker(
        table,
        model,
        only_include_views_which_want_realtime_events=True,
        updated_field_ids=updated_field_ids,
    )
    return {
        "old_row": _serialize_row(model, row),
        "old_row_public_views": row_checker.get_public_views_where_row_is_visible(row),
        "caching_row_checker": row_checker,
    }


@receiver(row_signals.row_updated)
def public_row_updated(
    sender, row, user, table, model, before_return, updated_field_ids, **kwargs
):
    before_return_dict = dict(before_return)[public_before_row_update]
    serialized_old_row = before_return_dict["old_row"]
    serialized_updated_row = _serialize_row(model, row)

    old_row_public_views = before_return_dict["old_row_public_views"]
    existing_checker = before_return_dict["caching_row_checker"]
    views = existing_checker.get_public_views_where_row_is_visible(row)
    updated_row_public_views = {view.slug: view for view in views}

    # When a row is updated from the point of view of a public view it might not always
    # result in a `row_updated` event. For example if the row was previously not visible
    # in the public view due to its filters, but the row update makes it now match
    # the filters we want to send a `row_created` event to that views page as the
    # clients won't know anything about the row and hence a `row_updated` event makes
    # no sense for them.

    public_views_where_row_was_deleted = []
    public_views_where_row_was_updated = []
    for old_row_view in old_row_public_views:
        updated_row_view = updated_row_public_views.pop(old_row_view.slug, None)
        if updated_row_view is None:
            # The updated row is no longer visible in `old_row_view` hence we should
            # send that view a deleted event.
            public_views_where_row_was_deleted.append(old_row_view)
        else:
            # The updated row is still visible so here we want a normal updated event.
            public_views_where_row_was_updated.append(old_row_view)
    # Any remaining views in the updated_row_public_views dict are views which
    # previously didn't show the old row, but now show the new row, so we want created.
    public_views_where_row_was_created = updated_row_public_views.values()

    def _send_created_updated_deleted_row_signals_to_views():
        _send_row_deleted_event_to_views(
            serialized_old_row, public_views_where_row_was_deleted
        )
        _send_row_created_event_to_views(
            serialized_updated_row,
            before=None,
            public_views=public_views_where_row_was_created,
        )

        view_page_type = page_registry.get("view")
        handler = ViewHandler()
        for public_view in public_views_where_row_was_updated:
            (
                visible_fields_only_updated_row,
                visible_fields_only_old_row,
            ) = handler.restrict_rows_for_view(
                public_view, [serialized_updated_row, serialized_old_row]
            )
            view_page_type.broadcast(
                RealtimeRowMessages.row_updated(
                    table_id=PUBLIC_PLACEHOLDER_ENTITY_ID,
                    serialized_row_before_update=visible_fields_only_old_row,
                    serialized_row=visible_fields_only_updated_row,
                    metadata={},
                ),
                slug=public_view.slug,
            )

    transaction.on_commit(_send_created_updated_deleted_row_signals_to_views)

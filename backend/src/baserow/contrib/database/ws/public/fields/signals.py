from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.api.views.serializers import PublicFieldSerializer
from baserow.contrib.database.fields import signals as field_signals
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.views.models import View
from baserow.contrib.database.views.registries import view_type_registry
from baserow.contrib.database.ws.fields.signals import RealtimeFieldMessages
from baserow.core.db import specific_iterator
from baserow.ws.registries import page_registry


def _broadcast_payload_to_views_with_restricted_related_fields(
    payload: Dict[str, Any],
    serialized_related_fields: List[Dict[str, Any]],
    views_with_hidden_fields: List[Tuple[View, Set[int]]],
):
    view_page_type = page_registry.get("view")
    for view, hidden_fields in views_with_hidden_fields:
        payload["related_fields"] = [
            f for f in serialized_related_fields if f["id"] not in hidden_fields
        ]
        view_page_type.broadcast(
            payload,
            None,
            slug=view.slug,
        )


def _send_payload_to_public_views_where_field_not_hidden(
    field: Field, payload: Dict[str, Any]
):
    related_fields = payload.pop("related_fields", [])
    related_field_ids = [f["id"] for f in related_fields]

    views_with_hidden_fields = _get_views_where_field_visible_and_hidden_fields_in_view(
        field,
        # Only bother calculating the hidden_fields set for the related_fields
        hidden_fields_field_ids_filter=related_field_ids,
    )
    _broadcast_payload_to_views_with_restricted_related_fields(
        payload, related_fields, views_with_hidden_fields
    )


def _get_views_where_field_visible_and_hidden_fields_in_view(
    field: Field,
    hidden_fields_field_ids_filter: Optional[Iterable[int]] = None,
) -> List[Tuple[View, Set[int]]]:
    """
    Finds all views where field is visible and also attaches the set of fields which
    are hidden in said view.

    :param field: All views where this field is visible will be returned.
    :param hidden_fields_field_ids_filter: An optional filter which restricts the
        calculation of whether a field is hidden or not in a returned view down to just
        checking the fields in this iterable.
    :return: A list of tuples where the first value is a view where field is visible
        and the second is the set of field ids which are hidden in said view.
    """

    views_with_prefetched_fields = View.objects.filter(
        public=True, table_id=field.table_id
    ).prefetch_related("table__field_set")

    specific_views = specific_iterator(
        views_with_prefetched_fields,
        per_content_type_queryset_hook=(
            lambda model, queryset: view_type_registry.get_by_model(
                model
            ).enhance_queryset(queryset)
        ),
    )
    if len(specific_views) == 0:
        return []

    if hidden_fields_field_ids_filter is None:
        table = specific_views[0].table
        all_field_ids = table.field_set.values_list("id", flat=True)
        restrict_hidden_check_to_field_ids = all_field_ids
    else:
        restrict_hidden_check_to_field_ids = [field.id, *hidden_fields_field_ids_filter]

    views_where_field_was_visible = []
    for view in specific_views:
        view = view.specific
        view_type = view_type_registry.get_by_model(view)
        if not view_type.when_shared_publicly_requires_realtime_events:
            continue

        hidden_field_ids = view_type.get_hidden_fields(
            view, restrict_hidden_check_to_field_ids
        )
        if field.id not in hidden_field_ids:
            views_where_field_was_visible.append((view, hidden_field_ids))
    return views_where_field_was_visible


@receiver(field_signals.field_created)
def public_field_created(sender, field, related_fields, user, **kwargs):
    transaction.on_commit(
        lambda: _send_payload_to_public_views_where_field_not_hidden(
            field,
            RealtimeFieldMessages.field_created(
                field, related_fields, field_serializer_class=PublicFieldSerializer
            ),
        )
    )


@receiver(field_signals.field_restored)
def public_field_restored(sender, field, related_fields, user, **kwargs):
    transaction.on_commit(
        lambda: _send_payload_to_public_views_where_field_not_hidden(
            field,
            RealtimeFieldMessages.field_restored(
                field, related_fields, field_serializer_class=PublicFieldSerializer
            ),
        )
    )


@receiver(field_signals.field_updated)
def public_field_updated(sender, field, related_fields, user, **kwargs):
    transaction.on_commit(
        lambda: _send_payload_to_public_views_where_field_not_hidden(
            field,
            RealtimeFieldMessages.field_updated(
                field, related_fields, field_serializer_class=PublicFieldSerializer
            ),
        )
    )


@receiver(field_signals.before_field_deleted)
def public_before_field_deleted(sender, field_id, field, user, **kwargs):
    # We have to check where the field is visible before it is deleted.
    return _get_views_where_field_visible_and_hidden_fields_in_view(
        field,
        # We don't know yet which fields will be related_fields so calculate the
        # hidden_fields set for all fields in the view as any could potentially be
        # a related_field.
        hidden_fields_field_ids_filter=None,
    )


@receiver(field_signals.field_deleted)
def public_field_deleted(
    sender, field_id, field, related_fields, user, before_return, **kwargs
):
    def send_deleted():
        views = dict(before_return)[public_before_field_deleted]
        payload = RealtimeFieldMessages.field_deleted(
            PUBLIC_PLACEHOLDER_ENTITY_ID,
            field_id,
            related_fields,
            field_serializer_class=PublicFieldSerializer,
        )
        serialized_related_fields = payload.pop("related_fields", [])

        _broadcast_payload_to_views_with_restricted_related_fields(
            payload, serialized_related_fields, views
        )

    transaction.on_commit(send_deleted)

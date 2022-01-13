from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.database.api.views.grid.serializers import PublicFieldSerializer
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.views import signals as view_signals
from baserow.contrib.database.views.registries import view_type_registry
from baserow.ws.registries import page_registry


def _send_force_rows_refresh_if_view_public(view):
    view_page_type = page_registry.get("view")
    if view.public:
        transaction.on_commit(
            lambda: view_page_type.broadcast(
                {"type": "force_view_rows_refresh", "view_id": view.slug},
                None,
                slug=view.slug,
            )
        )


@receiver(view_signals.view_updated)
def public_view_updated(sender, view, user, **kwargs):
    _send_force_rows_refresh_if_view_public(view)


@receiver(view_signals.view_filter_created)
def public_view_filter_created(sender, view_filter, user, **kwargs):
    _send_force_rows_refresh_if_view_public(view_filter.view)


@receiver(view_signals.view_filter_updated)
def public_view_filter_updated(sender, view_filter, user, **kwargs):
    _send_force_rows_refresh_if_view_public(view_filter.view)


@receiver(view_signals.view_filter_deleted)
def public_view_filter_deleted(sender, view_filter_id, view_filter, user, **kwargs):
    _send_force_rows_refresh_if_view_public(view_filter.view)


@receiver(view_signals.view_field_options_updated)
def public_view_field_options_updated(sender, view, user, **kwargs):
    if view.public:
        view = view.specific
        view_page_type = page_registry.get("view")
        view_type = view_type_registry.get_by_model(view)
        if not view_type.when_shared_publicly_requires_realtime_events:
            return

        field_options = view_type.get_visible_field_options_in_order(view)
        fields = [
            field_type_registry.get_serializer(o.field, PublicFieldSerializer).data
            for o in field_options.select_related("field")
        ]
        view_page_type.broadcast(
            {"type": "force_view_refresh", "view_id": view.slug, "fields": fields},
            None,
            slug=view.slug,
        )

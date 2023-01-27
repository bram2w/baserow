from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.database.api.views.serializers import (
    ViewDecorationSerializer,
    ViewFilterSerializer,
    ViewSerializer,
    ViewSortSerializer,
)
from baserow.contrib.database.views import signals as view_signals
from baserow.contrib.database.views.registries import (
    view_ownership_type_registry,
    view_type_registry,
)
from baserow.ws.registries import page_registry
from baserow.ws.tasks import broadcast_to_users


def broadcast_to(user, view, payload):
    ownership_type = view_ownership_type_registry.get(view.ownership_type)
    broadcast_type, params = ownership_type.should_broadcast_signal_to(view)

    if broadcast_type == "users":
        transaction.on_commit(
            lambda: broadcast_to_users.delay(
                params,
                payload,
                getattr(user, "web_socket_id", None),
            )
        )

    if broadcast_type == "table":
        table_page_type = page_registry.get("table")
        transaction.on_commit(
            lambda: table_page_type.broadcast(
                payload,
                getattr(user, "web_socket_id", None),
                table_id=view.table_id,
            )
        )


@receiver(view_signals.view_created)
def view_created(sender, view, user, **kwargs):
    payload = {
        "type": "view_created",
        "view": view_type_registry.get_serializer(
            view,
            ViewSerializer,
            filters=True,
            sortings=True,
            decorations=True,
        ).data,
    }

    broadcast_to(user, view, payload)


@receiver(view_signals.view_updated)
def view_updated(sender, view, user, **kwargs):
    payload = {
        "type": "view_updated",
        "view_id": view.id,
        "view": view_type_registry.get_serializer(
            view,
            ViewSerializer,
            # We do not want to broad cast the filters, decorations and sortings
            # every time the view changes.
            # There are separate views and handlers for them
            # each will broad cast their own message.
            filters=False,
            sortings=False,
            decorations=False,
        ).data,
    }

    broadcast_to(user, view, payload)


@receiver(view_signals.view_deleted)
def view_deleted(sender, view_id, view, user, **kwargs):
    payload = {"type": "view_deleted", "table_id": view.table_id, "view_id": view_id}

    broadcast_to(user, view, payload)


@receiver(view_signals.views_reordered)
def views_reordered(sender, table, order, user, **kwargs):
    payload = {"type": "views_reordered", "table_id": table.id, "order": order}

    first_view = table.view_set.get(id=order[0])

    # Here we are assuming that the views are all broadcasted the same way as they are
    # and there should be from the same "owner"
    broadcast_to(user, first_view, payload)


@receiver(view_signals.view_filter_created)
def view_filter_created(sender, view_filter, user, **kwargs):
    payload = {
        "type": "view_filter_created",
        "view_filter": ViewFilterSerializer(view_filter).data,
    }

    broadcast_to(user, view_filter.view, payload)


@receiver(view_signals.view_filter_updated)
def view_filter_updated(sender, view_filter, user, **kwargs):
    payload = {
        "type": "view_filter_updated",
        "view_filter_id": view_filter.id,
        "view_filter": ViewFilterSerializer(view_filter).data,
    }

    broadcast_to(user, view_filter.view, payload)


@receiver(view_signals.view_filter_deleted)
def view_filter_deleted(sender, view_filter_id, view_filter, user, **kwargs):
    payload = {
        "type": "view_filter_deleted",
        "view_id": view_filter.view_id,
        "view_filter_id": view_filter_id,
    }

    broadcast_to(user, view_filter.view, payload)


@receiver(view_signals.view_sort_created)
def view_sort_created(sender, view_sort, user, **kwargs):
    payload = {
        "type": "view_sort_created",
        "view_sort": ViewSortSerializer(view_sort).data,
    }

    broadcast_to(user, view_sort.view, payload)


@receiver(view_signals.view_sort_updated)
def view_sort_updated(sender, view_sort, user, **kwargs):
    payload = {
        "type": "view_sort_updated",
        "view_sort_id": view_sort.id,
        "view_sort": ViewSortSerializer(view_sort).data,
    }

    broadcast_to(user, view_sort.view, payload)


@receiver(view_signals.view_sort_deleted)
def view_sort_deleted(sender, view_sort_id, view_sort, user, **kwargs):
    payload = {
        "type": "view_sort_deleted",
        "view_id": view_sort.view_id,
        "view_sort_id": view_sort_id,
    }

    broadcast_to(user, view_sort.view, payload)


@receiver(view_signals.view_decoration_created)
def view_decoration_created(sender, view_decoration, user, **kwargs):
    payload = {
        "type": "view_decoration_created",
        "view_decoration": ViewDecorationSerializer(view_decoration).data,
    }

    broadcast_to(user, view_decoration.view, payload)


@receiver(view_signals.view_decoration_updated)
def view_decoration_updated(sender, view_decoration, user, **kwargs):
    payload = {
        "type": "view_decoration_updated",
        "view_decoration_id": view_decoration.id,
        "view_decoration": ViewDecorationSerializer(view_decoration).data,
    }

    broadcast_to(user, view_decoration.view, payload)


@receiver(view_signals.view_decoration_deleted)
def view_decoration_deleted(
    sender, view_decoration_id, view_decoration, user, **kwargs
):
    payload = {
        "type": "view_decoration_deleted",
        "view_id": view_decoration.view_id,
        "view_decoration_id": view_decoration_id,
    }

    broadcast_to(user, view_decoration.view, payload)


@receiver(view_signals.view_field_options_updated)
def view_field_options_updated(sender, view, user, **kwargs):
    view_type = view_type_registry.get_by_model(view.specific_class)
    serializer_class = view_type.get_field_options_serializer_class(
        create_if_missing=False
    )
    payload = {
        "type": "view_field_options_updated",
        "view_id": view.id,
        "field_options": serializer_class(view).data["field_options"],
    }

    broadcast_to(user, view, payload)

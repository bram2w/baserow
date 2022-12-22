from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.database.api.tables.serializers import TableSerializer
from baserow.contrib.database.table import signals as table_signals
from baserow.contrib.database.table.tasks import (
    unsubscribe_user_from_table_currently_subscribed_to,
)
from baserow.core import signals as core_signals
from baserow.ws.tasks import broadcast_to_group


@receiver(table_signals.table_created)
def table_created(sender, table, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            table.database.group_id,
            {"type": "table_created", "table": TableSerializer(table).data},
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(table_signals.table_updated)
def table_updated(sender, table, user, force_table_refresh=False, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            table.database.group_id,
            {
                "type": "table_updated",
                "table_id": table.id,
                "table": TableSerializer(table).data,
                "force_table_refresh": force_table_refresh,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(table_signals.table_deleted)
def table_deleted(sender, table_id, table, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            table.database.group_id,
            {
                "type": "table_deleted",
                "database_id": table.database_id,
                "table_id": table_id,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(table_signals.tables_reordered)
def tables_reordered(sender, database, order, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            database.group_id,
            {
                "type": "tables_reordered",
                "database_id": database.id,
                "order": order,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(core_signals.group_user_deleted)
def user_deleted_unsubscribe_from_page(
    sender, group_user_id, group_user, user, **kwargs
):
    transaction.on_commit(
        lambda: unsubscribe_user_from_table_currently_subscribed_to.delay(
            group_user.user_id, group_user.group_id
        )
    )

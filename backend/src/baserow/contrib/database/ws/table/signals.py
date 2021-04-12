from django.dispatch import receiver
from django.db import transaction

from baserow.contrib.database.table import signals as table_signals
from baserow.contrib.database.api.tables.serializers import TableSerializer

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
def table_updated(sender, table, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            table.database.group_id,
            {
                "type": "table_updated",
                "table_id": table.id,
                "table": TableSerializer(table).data,
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

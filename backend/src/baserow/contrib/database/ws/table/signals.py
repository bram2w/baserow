from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.database.api.tables.serializers import TableSerializer
from baserow.contrib.database.table import signals as table_signals
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.table.object_scopes import DatabaseTableObjectScopeType
from baserow.contrib.database.table.operations import ReadDatabaseTableOperationType
from baserow.contrib.database.table.tasks import (
    unsubscribe_user_from_tables_when_removed_from_workspace,
)
from baserow.core import signals as core_signals
from baserow.core.utils import generate_hash
from baserow.ws.tasks import broadcast_to_group, broadcast_to_permitted_users


@receiver(table_signals.table_created)
def table_created(sender, table, user, **kwargs):
    transaction.on_commit(
        lambda: broadcast_to_permitted_users.delay(
            table.database.workspace_id,
            ReadDatabaseTableOperationType.type,
            DatabaseTableObjectScopeType.type,
            table.id,
            {"type": "table_created", "table": TableSerializer(table).data},
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(table_signals.table_updated)
def table_updated(
    sender,
    table: Table,
    user: AbstractUser,
    force_table_refresh: bool = False,
    **kwargs,
):
    transaction.on_commit(
        lambda: broadcast_to_permitted_users.delay(
            table.database.workspace_id,
            ReadDatabaseTableOperationType.type,
            DatabaseTableObjectScopeType.type,
            table.id,
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
        lambda: broadcast_to_permitted_users.delay(
            table.database.workspace_id,
            ReadDatabaseTableOperationType.type,
            DatabaseTableObjectScopeType.type,
            table.id,
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
    # Hashing all values here to not expose real ids of tables a user might not have
    # access to
    order = [generate_hash(o) for o in order]
    transaction.on_commit(
        lambda: broadcast_to_group.delay(
            database.workspace_id,
            {
                "type": "tables_reordered",
                # A user might also not have access to the database itself
                "database_id": generate_hash(database.id),
                "order": order,
            },
            getattr(user, "web_socket_id", None),
        )
    )


@receiver(core_signals.workspace_user_deleted)
def workspace_user_deleted(sender, workspace_user_id, workspace_user, user, **kwargs):
    transaction.on_commit(
        lambda: unsubscribe_user_from_tables_when_removed_from_workspace.delay(
            workspace_user.user_id, workspace_user.workspace_id
        )
    )

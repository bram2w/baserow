from baserow.core.object_scopes import ApplicationObjectScopeType
from baserow.core.registries import OperationType


class SnapshotOperationType(OperationType):
    context_scope_name = "snapshot"


class ListSnapshotsApplicationOperationType(ApplicationObjectScopeType):
    type = "database.list_snapshots"
    object_scope_name = "snapshot"


class CreateSnapshotApplicationOperationType(ApplicationObjectScopeType):
    type = "database.create_snapshot"


class RestoreApplicationSnapshotOperationType(SnapshotOperationType):
    type = "database.snapshot.restore"


class DeleteApplicationSnapshotOperationType(SnapshotOperationType):
    type = "database.snapshot.delete"

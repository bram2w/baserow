import abc

from baserow.core.operations import ApplicationOperationType
from baserow.core.registries import OperationType


class SnapshotOperationType(OperationType, abc.ABC):
    context_scope_name = "snapshot"


class ListSnapshotsApplicationOperationType(ApplicationOperationType):
    type = "application.list_snapshots"
    object_scope_name = "snapshot"


class CreateSnapshotApplicationOperationType(ApplicationOperationType):
    type = "application.create_snapshot"


class RestoreApplicationSnapshotOperationType(SnapshotOperationType):
    type = "application.snapshot.restore"


class DeleteApplicationSnapshotOperationType(SnapshotOperationType):
    type = "application.snapshot.delete"

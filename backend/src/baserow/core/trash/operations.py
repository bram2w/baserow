from baserow.core.operations import ApplicationOperationType, WorkspaceCoreOperationType


class ReadWorkspaceTrashOperationType(WorkspaceCoreOperationType):
    type = "workspace.read_trash"


class ReadApplicationTrashOperationType(ApplicationOperationType):
    type = "application.read_trash"


class EmptyWorkspaceTrashOperationType(WorkspaceCoreOperationType):
    type = "workspace.empty_trash"


class EmptyApplicationTrashOperationType(ApplicationOperationType):
    type = "application.empty_trash"

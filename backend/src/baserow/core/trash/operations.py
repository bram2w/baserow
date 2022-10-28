from baserow.core.operations import ApplicationOperationType, GroupCoreOperationType


class ReadGroupTrashOperationType(GroupCoreOperationType):
    type = "group.read_trash"


class ReadApplicationTrashOperationType(ApplicationOperationType):
    type = "application.read_trash"


class EmptyGroupTrashOperationType(GroupCoreOperationType):
    type = "group.empty_trash"


class EmptyApplicationTrashOperationType(ApplicationOperationType):
    type = "application.empty_trash"

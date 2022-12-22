from baserow.contrib.database.table.operations import DatabaseTableOperationType
from baserow.core.operations import ApplicationOperationType, GroupCoreOperationType


class AssignRoleGroupOperationType(GroupCoreOperationType):
    type = "group.assign_role"


class ReadRoleGroupOperationType(GroupCoreOperationType):
    type = "group.read_role"


class ReadRoleApplicationOperationType(ApplicationOperationType):
    type = "application.read_role"


class UpdateRoleApplicationOperationType(ApplicationOperationType):
    type = "application.update_role"


class ReadRoleTableOperationType(DatabaseTableOperationType):
    type = "database.table.read_role"


class UpdateRoleTableOperationType(DatabaseTableOperationType):
    type = "database.table.update_role"

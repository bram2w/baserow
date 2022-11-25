from baserow.contrib.database.operations import DatabaseOperationType
from baserow.contrib.database.table.operations import DatabaseTableOperationType
from baserow.core.operations import GroupCoreOperationType


class AssignRoleGroupOperationType(GroupCoreOperationType):
    type = "group.assign_role"


class ReadRoleGroupOperationType(GroupCoreOperationType):
    type = "group.read_role"


class ReadRoleDatabaseOperationType(DatabaseOperationType):
    type = "database.read_role"


class UpdateRoleDatabaseOperationType(DatabaseOperationType):
    type = "database.update_role"


class ReadRoleTableOperationType(DatabaseTableOperationType):
    type = "database.table.read_role"


class UpdateRoleTableOperationType(DatabaseTableOperationType):
    type = "database.table.update_role"

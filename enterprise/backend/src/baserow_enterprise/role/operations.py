from baserow.core.registries import OperationType


class AssignRoleGroupOperationType(OperationType):
    type = "group.assign_role"
    context_scope_name = "group"

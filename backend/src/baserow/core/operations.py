from abc import ABC

from baserow.core.registries import OperationType


class CoreOperationType(OperationType, ABC):
    context_scope_name = "core"


class UpdateSettingsOperationType(CoreOperationType):
    type = "settings.update"


class CreateGroupOperationType(CoreOperationType):
    type = "create_group"


class ListGroupsOperationType(CoreOperationType):
    type = "list_groups"
    object_scope_name = "group"


class GroupCoreOperationType(CoreOperationType, ABC):
    context_scope_name = "group"


class ReadGroupOperationType(GroupCoreOperationType):
    type = "group.read"


class UpdateGroupOperationType(GroupCoreOperationType):
    type = "group.update"


class DeleteGroupOperationType(GroupCoreOperationType):
    type = "group.delete"


class RestoreGroupOperationType(GroupCoreOperationType):
    type = "group.restore"


class ListApplicationsGroupOperationType(GroupCoreOperationType):
    type = "group.list_applications"
    object_scope_name = "application"


class CreateApplicationsGroupOperationType(GroupCoreOperationType):
    type = "group.create_application"


class OrderApplicationsOperationType(GroupCoreOperationType):
    type = "group.order_applications"


class CreateInvitationsGroupOperationType(GroupCoreOperationType):
    type = "group.create_invitation"


class ListInvitationsGroupOperationType(GroupCoreOperationType):
    type = "group.list_invitations"
    object_scope_name = "group_invitation"


class ListGroupUsersGroupOperationType(GroupCoreOperationType):
    type = "group.list_group_users"
    object_scope_name = "group_user"


class InvitationGroupOperationType(CoreOperationType, ABC):
    context_scope_name = "group_invitation"


class ReadInvitationGroupOperationType(InvitationGroupOperationType):
    type = "invitation.read"


class UpdateGroupInvitationType(InvitationGroupOperationType):
    type = "invitation.update"


class DeleteGroupInvitationOperationType(InvitationGroupOperationType):
    type = "invitation.delete"


class GroupUserOperationType(OperationType, ABC):
    context_scope_name = "group_user"


class UpdateGroupUserOperationType(GroupUserOperationType):
    type = "group_user.update"


class DeleteGroupUserOperationType(GroupUserOperationType):
    type = "group_user.delete"


class ApplicationOperationType(OperationType, ABC):
    context_scope_name = "application"


class ReadApplicationOperationType(ApplicationOperationType):
    type = "application.read"


class UpdateApplicationOperationType(ApplicationOperationType):
    type = "application.update"


class DuplicateApplicationOperationType(ApplicationOperationType):
    type = "application.duplicate"


class DeleteApplicationOperationType(ApplicationOperationType):
    type = "application.delete"


class RestoreApplicationOperationType(ApplicationOperationType):
    type = "application.restore"

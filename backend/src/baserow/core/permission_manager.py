from rest_framework.exceptions import NotAuthenticated

from baserow.core.models import GroupUser

from .exceptions import (
    IsNotAdminError,
    UserInvalidGroupPermissionsError,
    UserNotInGroup,
)
from .operations import (
    CreateGroupOperationType,
    CreateInvitationsGroupOperationType,
    DeleteGroupInvitationOperationType,
    DeleteGroupOperationType,
    DeleteGroupUserOperationType,
    ListGroupsOperationType,
    ListGroupUsersGroupOperationType,
    ListInvitationsGroupOperationType,
    ReadInvitationGroupOperationType,
    UpdateGroupInvitationType,
    UpdateGroupOperationType,
    UpdateGroupUserOperationType,
    UpdateSettingsOperationType,
)
from .registries import PermissionManagerType


class CorePermissionManagerType(PermissionManagerType):
    """
    Some operation are always allowed. This permission manager handle this case.
    """

    type = "core"

    ALWAYS_ALLOWED_OPERATIONS = [
        CreateGroupOperationType.type,
        ListGroupsOperationType.type,
    ]

    def check_permissions(
        self, actor, operation, group=None, context=None, include_trash=False
    ):

        if operation in self.ALWAYS_ALLOWED_OPERATIONS:
            return True

    def get_permissions_object(self, actor, group=None):
        return self.ALWAYS_ALLOWED_OPERATIONS


class StaffOnlyPermissionManagerType(PermissionManagerType):
    """
    Checks if a user is_staff if the required operation is for staff only.
    """

    type = "staff"
    STAFF_ONLY_OPERATIONS = [UpdateSettingsOperationType.type]

    def check_permissions(
        self, actor, operation, group=None, context=None, include_trash=False
    ):

        if hasattr(actor, "is_authenticated"):
            user = actor
            if not user.is_authenticated:
                raise NotAuthenticated()

            if operation in self.STAFF_ONLY_OPERATIONS:
                if actor.is_staff:
                    return True
                else:
                    raise IsNotAdminError(user)

    def get_permissions_object(self, actor, group=None):
        return {
            "staff_only_operations": self.STAFF_ONLY_OPERATIONS,
            "is_staff": actor.is_staff,
        }


class GroupMemberOnlyPermissionManagerType(PermissionManagerType):
    """
    To be able to operate on a group, the user must at least belongs to that group.
    """

    type = "member"

    def check_permissions(
        self, actor, operation, group=None, context=None, include_trash=False
    ):
        if group is None:
            return None

        if hasattr(actor, "is_authenticated"):
            user = actor
            if not user.is_authenticated:
                raise NotAuthenticated()

            if include_trash:
                queryset = GroupUser.objects_and_trash
            else:
                queryset = GroupUser.objects

            # Check if the user is a member of this group
            if not queryset.filter(user_id=user.id, group_id=group.id).exists():
                raise UserNotInGroup(user, group)

    def get_permissions_object(self, actor, group=None):
        # Check if the user is a member of this group
        if GroupUser.objects.filter(user_id=actor.id, group_id=group.id).exists():
            return None
        return False


class BasicPermissionManagerType(PermissionManagerType):
    """
    This permission manager check if the user is an admin when the operation is admin
    only.
    """

    type = "basic"

    ADMIN_ONLY_OPERATIONS = [
        ListInvitationsGroupOperationType.type,
        CreateInvitationsGroupOperationType.type,
        ReadInvitationGroupOperationType.type,
        UpdateGroupInvitationType.type,
        DeleteGroupInvitationOperationType.type,
        ListGroupUsersGroupOperationType.type,
        UpdateGroupOperationType.type,
        DeleteGroupOperationType.type,
        UpdateGroupUserOperationType.type,
        DeleteGroupUserOperationType.type,
    ]

    def check_permissions(
        self, actor, operation, group=None, context=None, include_trash=False
    ):

        if group is None:
            return None

        if hasattr(actor, "is_authenticated"):
            user = actor
            if not user.is_authenticated:
                raise NotAuthenticated()

            if operation in self.ADMIN_ONLY_OPERATIONS:

                if include_trash:
                    manager = GroupUser.objects_and_trash
                else:
                    manager = GroupUser.objects

                queryset = manager.filter(user_id=user.id, group_id=group.id)

                # Check if the user is a member of this group
                group_user = queryset.get()

                if "ADMIN" not in group_user.permissions:
                    raise UserInvalidGroupPermissionsError(user, group, operation)

            return True

    def get_permissions_object(self, actor, group=None, include_trash=False):
        if group is None:
            return None

        if include_trash:
            manager = GroupUser.objects_and_trash
        else:
            manager = GroupUser.objects

        queryset = manager.filter(user_id=actor.id, group_id=group.id)

        try:
            # Check if the user is a member of this group
            group_user = queryset.get()
        except GroupUser.DoesNotExist:
            return None

        return {
            "admin_only_operations": self.ADMIN_ONLY_OPERATIONS,
            "is_admin": "ADMIN" in group_user.permissions,
        }

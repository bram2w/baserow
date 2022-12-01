import dataclasses
from typing import Any, Optional

from django.contrib.auth.models import AbstractUser

from baserow_premium.license.handler import LicenseHandler

from baserow.contrib.database.views.models import ViewFilter
from baserow.core.action.models import Action
from baserow.core.action.registries import ActionScopeStr, ActionType
from baserow.core.action.scopes import GroupActionScopeType
from baserow.core.handler import CoreHandler
from baserow.core.models import Group
from baserow.core.registries import (
    object_scope_type_registry,
    permission_manager_type_registry,
    subject_type_registry,
)
from baserow_enterprise.features import RBAC
from baserow_enterprise.role.exceptions import CantLowerAdminsRoleOnChildException
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role
from baserow_enterprise.role.permission_manager import RolePermissionManagerType


class AssignRoleActionType(ActionType):
    type = "assign_role"

    @dataclasses.dataclass
    class Params:
        subject_id: int
        subject_type: str
        group_id: int
        role_uid: Optional[str]
        original_role_uid: Optional[str]
        scope_id: int
        scope_type: str

    @classmethod
    def do(
        cls,
        user,
        subject,
        group: Group,
        role: Optional[Role] = None,
        scope: Optional[Any] = None,
    ) -> ViewFilter:
        """
        Assigns a role to a subject into a group over a given scope.

        :param subject: The subject targeted by the role.
        :param group: The group in which we want to assign the role.
        :param role: The role we want to assign. If the role is `None` then we remove
            the current role of the subject in the group for the given scope.
        :param scope: An optional scope on which the role applies. If no scope is given
            the group is used as scope.
        :return: The created RoleAssignment if role is not `None` else `None`.
        """

        if scope is None:
            scope = group

        LicenseHandler.raise_if_user_doesnt_have_feature(RBAC, user, group)

        role_permission_manager = permission_manager_type_registry.get_by_type(
            RolePermissionManagerType
        )

        scope_type = object_scope_type_registry.get_by_model(scope)
        CoreHandler().check_permissions(
            user,
            role_permission_manager.role_assignable_object_map[scope_type.type][
                "UPDATE"
            ].type,
            group=group,
            context=scope,
        )

        role_assignment_handler = RoleAssignmentHandler()

        previous_role = role_assignment_handler.get_current_role_assignment(
            subject, group, scope=scope
        )

        def has_parent_with_admin_role():
            parent = object_scope_type_registry.get_parent(scope)
            return (
                parent is not None
                and role_assignment_handler.get_computed_role(
                    group, subject, parent
                ).uid
                == role_assignment_handler.ADMIN_ROLE
            )

        # Check if the role assignment is not an exception for a scope under another
        # scope targeted by an ADMIN role.
        if role is not None and has_parent_with_admin_role():
            raise CantLowerAdminsRoleOnChildException()

        role_assignment = role_assignment_handler.assign_role(
            subject,
            group,
            role,
            scope=scope,
        )

        scope_type = object_scope_type_registry.get_by_model(scope).type
        subject_type = subject_type_registry.get_by_model(subject).type

        cls.register_action(
            user=user,
            params=cls.Params(
                subject.id,
                subject_type,
                group.id,
                role.uid if role else None,
                previous_role.role.uid if previous_role else None,
                scope.id,
                scope_type,
            ),
            scope=cls.scope(group.id),
        )
        return role_assignment

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):

        role_assignment_handler = RoleAssignmentHandler()
        group = Group.objects.get(id=params.group_id)
        scope = role_assignment_handler.get_scope(params.scope_id, params.scope_type)

        LicenseHandler.raise_if_user_doesnt_have_feature(RBAC, user, group)
        role_permission_manager = permission_manager_type_registry.get_by_type(
            RolePermissionManagerType
        )

        scope_type = object_scope_type_registry.get_by_model(scope)
        CoreHandler().check_permissions(
            user,
            role_permission_manager.role_assignable_object_map[scope_type.type][
                "UPDATE"
            ].type,
            group=group,
            context=scope,
        )

        subject = role_assignment_handler.get_subject(
            params.subject_id, params.subject_type
        )

        role = (
            role_assignment_handler.get_role_by_uid(params.original_role_uid)
            if params.original_role_uid
            else None
        )

        role_assignment_handler.assign_role(
            subject,
            group,
            role,
            scope=scope,
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):

        role_assignment_handler = RoleAssignmentHandler()

        group = Group.objects.get(id=params.group_id)
        scope = role_assignment_handler.get_scope(params.scope_id, params.scope_type)

        LicenseHandler.raise_if_user_doesnt_have_feature(RBAC, user, group)
        scope_type = object_scope_type_registry.get_by_model(scope)
        role_permission_manager = permission_manager_type_registry.get_by_type(
            RolePermissionManagerType
        )

        CoreHandler().check_permissions(
            user,
            role_permission_manager.role_assignable_object_map[scope_type.type][
                "UPDATE"
            ].type,
            group=group,
            context=scope,
        )

        subject = role_assignment_handler.get_subject(
            params.subject_id, params.subject_type
        )

        role = (
            role_assignment_handler.get_role_by_uid(params.role_uid)
            if params.role_uid
            else None
        )

        role_assignment_handler.assign_role(
            subject,
            group,
            role,
            scope=scope,
        )

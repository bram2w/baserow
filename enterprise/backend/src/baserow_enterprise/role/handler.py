from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType

from baserow.core.handler import CoreHandler
from baserow.core.models import Group, GroupUser
from baserow.core.registries import object_scope_type_registry
from baserow_enterprise.models import RoleAssignment
from baserow_enterprise.role.models import Role

User = get_user_model()

USER_TYPE = "auth.User"


class RoleAssignmentHandler:
    _role_cache_by_uid: Dict[str, List[str]] = {}
    role_fallback = "NO_ROLE"

    def get_role(self, role_uid: str = None) -> Role:
        """
        Returns the role for the given uid. This method is memoized.

        :param role_uid: The uid we want the role for.
        :return: A role.
        """

        if role_uid == "MEMBER":
            role_uid = "BUILDER"

        if role_uid not in self._role_cache_by_uid:
            try:
                self._role_cache_by_uid[role_uid] = Role.objects.get(uid=role_uid)
            except Role.DoesNotExist:
                return self.get_role(self.role_fallback)

        return self._role_cache_by_uid[role_uid]

    def get_current_role_assignment(
        self,
        subject: AbstractUser,
        group: Group,
        scope: Optional[Any] = None,
    ) -> RoleAssignment:
        """
        Returns the current assigned role for the given Group/Subject/Scope.

        :param subject: The subject we want the role for.
        :param group: The group in which you want the user role.
        :param scope: Un optional scope on which the role applies.
        :return: The current `RoleAssignment` or `None` if no role is defined for the
            given parameters.
        """

        if scope is None:
            scope = group

        content_types = ContentType.objects.get_for_models(scope, subject)

        if scope == group:
            try:
                group_user = GroupUser.objects.get(user=subject, group=group)
                role_uid = group_user.permissions
                role = self.get_role(role_uid)
                # We need to fake a RoleAssignment instance here to keep the same
                # return interface
                return RoleAssignment(
                    subject=subject,
                    subject_id=subject.id,
                    subject_type=content_types[subject],
                    role=role,
                    group=group,
                    scope=scope,
                    scope_type=content_types[scope],
                )
            except GroupUser.DoesNotExist:
                return None

        try:
            role_assignment = RoleAssignment.objects.get(
                scope_id=scope.id,
                scope_type=content_types[scope],
                group=group,
                subject_id=subject.id,
                subject_type=content_types[subject],
            )

            return role_assignment
        except RoleAssignment.DoesNotExist:
            return None

    def assign_role(
        self,
        subject,
        group,
        role=None,
        scope=None,
    ) -> Optional[RoleAssignment]:
        """
        Assign a role to a subject in the context of the given group over a specified
        scope.

        :param subject: The subject targeted by the role.
        :param group: The group in which we want to assign the role.
        :param role: The role we want to assign. If the role is `None` then we remove
            the current role of the subject in the group for the given scope.
        :param scope: An optional scope on which the role applies. If no scope is given
            the group is used as scope.
        :return: The created RoleAssignment if role is not `None` else `None`.
        """

        if role is None:
            # Early return, we are removing the current role.
            self.remove_role(subject, group, scope=scope)
            return

        if scope is None:
            scope = group

        content_types = ContentType.objects.get_for_models(scope, subject)

        # Group level permissions are not stored as RoleAssignment records
        if scope == group:
            group_user = GroupUser.objects.get(group=group, user=subject)
            new_permissions = "MEMBER" if role.uid == "BUILDER" else role.uid
            CoreHandler().force_update_group_user(
                None, group_user, permissions=new_permissions
            )

            # We need to fake a RoleAssignment instance here to keep the same
            # return interface
            return RoleAssignment(
                subject=subject,
                subject_id=subject.id,
                subject_type=content_types[subject],
                role=role,
                group=group,
                scope=scope,
                scope_type=content_types[scope],
            )

        role_assignment, _ = RoleAssignment.objects.update_or_create(
            subject_id=subject.id,
            subject_type=content_types[subject],
            group=group,
            scope_id=scope.id,
            scope_type=content_types[scope],
            defaults={"role": role},
        )

        return role_assignment

    def remove_role(self, subject: AbstractUser, group: Group, scope=None):
        """
        Remove the role of a subject in the context of the given group over a specified
        scope.

        :param subject: The subject for whom we want to remove the role for.
        :param group: The group in which we want to remove the role.
        :param scope: An optional scope on which the existing role applied.
            If no scope is given the group is used as scope.
        """

        if scope is None:
            scope = group

        if scope == group:
            GroupUser.objects.filter(user=subject, group=group).update(
                permissions="NO_ROLE"
            )

        content_types = ContentType.objects.get_for_models(scope, subject)

        RoleAssignment.objects.filter(
            subject_id=subject.id,
            subject_type=content_types[subject],
            group=group,
            scope_id=scope.id,
            scope_type=content_types[scope],
        ).delete()

    def get_subject(self, subject_id: int, subject_type: str):
        """
        Helper method that returns the actual subject object given the subject_id and
        the subject type.

        :param subject_id: The subject id.
        :param subject_type: The subject type.
        """

        if subject_type == USER_TYPE:
            content_type = ContentType.objects.get_for_model(User)
            return content_type.get_object_for_this_type(id=subject_id)

        return None

    def get_scope(self, scope_id: int, scope_type: str):
        """
        Helper method that returns the actual scope object given the scope ID and
        the scope type.

        :param scope_id: The scope id.
        :param scope_type: The scope type. This type must be registered in the
            `object_scope_registry`.
        """

        scope_type = object_scope_type_registry.get(scope_type)
        content_type = ContentType.objects.get_for_model(scope_type.model_class)
        return content_type.get_object_for_this_type(id=scope_id)

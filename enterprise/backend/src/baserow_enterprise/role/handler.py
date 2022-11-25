from typing import Any, Dict, List, Optional, Union

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType

from baserow.core.handler import CoreHandler
from baserow.core.models import Group, GroupUser
from baserow.core.registries import (
    object_scope_type_registry,
    permission_manager_type_registry,
    subject_type_registry,
)
from baserow_enterprise.exceptions import ScopeNotExist, SubjectNotExist
from baserow_enterprise.models import RoleAssignment
from baserow_enterprise.role.models import Role
from baserow_enterprise.teams.models import Team

User = get_user_model()


class RoleAssignmentHandler:
    _role_cache_by_uid: Dict[str, List[str]] = {}
    role_fallback = "NO_ROLE"

    def get_role(self, role_uid: str = None) -> Role:
        """
        Returns the role for the given uid.

        This method is memoized.

        :param role_uid: The uid we want the role for.
        :return: A role.
        """

        if role_uid == "MEMBER":
            role_uid = "BUILDER"

        if role_uid not in self._role_cache_by_uid:
            self._role_cache_by_uid[role_uid] = Role.objects.get(uid=role_uid)

        return self._role_cache_by_uid[role_uid]

    def get_role_or_fallback(self, role_uid: str = None) -> Role:
        """
        Returns the role for the given uid.
        If `role_uid` isn't found, we fall back to `role_fallback`.

        :param role_uid: The uid we want the role for.
        :return: A role.
        """

        try:
            return self.get_role(role_uid)
        except Role.DoesNotExist:
            # If `role_fallback` doesn't exist, raise.
            if role_uid == self.role_fallback:
                raise
            return self.get_role(self.role_fallback)

    def get_current_role_assignment(
        self,
        subject: Union[AbstractUser, Team],
        group: Group,
        scope: Optional[Any] = None,
    ) -> Union[RoleAssignment, None]:
        """
        Returns the current assigned role for the given Group/Subject/Scope.

        :param subject: The subject we want the role for.
        :param group: The group in which you want the user or team role.
        :param scope: An optional scope on which the role applies.
        :return: The current `RoleAssignment` or `None` if no role is defined for the
            given parameters.
        """

        if scope is None:
            scope = group

        content_types = ContentType.objects.get_for_models(scope, subject)

        # TODO: a comment on why we short-circuit here.
        if (
            isinstance(scope, Group)
            and scope.id == group.id
            and isinstance(subject, User)
        ):
            try:
                group_user = GroupUser.objects.get(user=subject, group=group)
                role_uid = group_user.permissions
                role = self.get_role_or_fallback(role_uid)
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
            role_assignment = RoleAssignment.objects.select_related("role").get(
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

        subject_type = subject_type_registry.get_by_model(subject)
        if not subject_type.is_in_group(subject.id, group):
            raise SubjectNotExist()

        if not object_scope_type_registry.scope_includes_context(group, scope):
            raise ScopeNotExist()

        content_types = ContentType.objects.get_for_models(scope, subject)

        # Group level permissions are not stored as RoleAssignment records
        if (
            isinstance(scope, Group)
            and scope.id == group.id
            and isinstance(subject, User)
        ):
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

    def remove_role(self, subject: Union[AbstractUser, Team], group: Group, scope=None):
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

        if (
            isinstance(scope, Group)
            and scope.id == group.id
            and isinstance(subject, User)
        ):
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

        content_type = subject_type_registry.get(subject_type).get_content_type()
        return content_type.get_object_for_this_type(id=subject_id)

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

    def assign_role_batch(
        self, user: AbstractUser, group: Group, values: List[Dict[str, any]]
    ):
        """
        Creates role assignments in batch, this should be used if many role assignments
        are created at once, to be more efficient.

        :return:
        """

        from baserow_enterprise.role.permission_manager import RolePermissionManagerType

        role_assignments = []
        role_assignments_to_create = []
        group_users_to_update_values = []

        no_role_role = Role.objects.get(uid="NO_ROLE")

        role_permission_manager = permission_manager_type_registry.get_by_type(
            RolePermissionManagerType
        )

        for value in values:
            if value["scope"] is None:
                value["scope"] = group

            scope_type = object_scope_type_registry.get_by_model(value["scope"])
            subject_type = subject_type_registry.get_by_model(value["subject"])

            if not subject_type.is_in_group(value["subject_id"], group):
                raise SubjectNotExist()

            if not object_scope_type_registry.scope_includes_context(
                group, value["scope"]
            ):
                raise ScopeNotExist()

            # TODO performance bottleneck
            CoreHandler().check_permissions(
                user,
                role_permission_manager.role_assignable_object_map[scope_type.type][
                    "READ"
                ].type,
                group=group,
                context=value["scope"],
            )

            role_assignment = RoleAssignment(
                subject=value["subject"],
                subject_id=value["subject_id"],
                subject_type=value["subject_type"],
                role=value["role"],
                scope=value["scope"],
                scope_id=value["scope_id"],
                scope_type=value["scope_type"],
                group=group,
            )

            if value["scope"] == group:  # Group level permissions
                if value["role"] is None:
                    value["role"] = no_role_role
                group_users_to_update_values.append(value)
            else:  # Not a group level assignment
                if value["role"] is None:  # Delete role assignment
                    self.remove_role(value["subject"], group, scope=value["scope"])
                else:  # Create or update role assignments
                    role_assignment_found = RoleAssignment.objects.filter(
                        subject_id=value["subject_id"],
                        subject_type=value["subject_type"],
                        scope_id=value["scope_id"],
                        scope_type=value["scope_type"],
                        group=group,
                    ).first()

                    if role_assignment_found:
                        role_assignment_found.role = value["role"]
                        role_assignment_found.save()
                    else:
                        role_assignments_to_create.append(role_assignment)

                    role_assignments.append(role_assignment)

        group_users_to_update_instances = GroupUser.objects.filter(
            group=group,
            user__in=[value["subject"] for value in group_users_to_update_values],
        )

        group_users_to_update_instances_map = {
            getattr(group_user.user, "id"): group_user
            for group_user in group_users_to_update_instances
        }

        for value in group_users_to_update_values:
            group_users_to_update_instances_map[
                value["subject_id"]
            ].permissions = value["role"].uid

        GroupUser.objects.bulk_update(
            group_users_to_update_instances_map.values(), ["permissions"]
        )
        RoleAssignment.objects.bulk_create(role_assignments_to_create)

        return role_assignments

    def get_role_assignments(self, group: Group, scope=None):
        """
        Helper method that returns all role assignments given a scope and group.

        :param group: The group that the scope belongs to
        :param scope: The scope used for filtering role assignments
        """

        if isinstance(scope, Group) and scope.id == group.id:
            group_users = GroupUser.objects.filter(group=group)

            role_assignments = []

            for group_user in group_users:
                role_uid = group_user.permissions
                role = self.get_role(role_uid)
                subject = group_user.user

                # TODO we probably shouldn't do this in a loop (performance)
                content_types = ContentType.objects.get_for_models(scope, subject)
                # We need to fake a RoleAssignment instance here to keep the same
                # return interface
                role_assignments.append(
                    RoleAssignment(
                        subject=subject,
                        subject_id=subject.id,
                        subject_type=content_types[subject],
                        role=role,
                        group=group,
                        scope=scope,
                        scope_type=content_types[scope],
                    )
                )
            return role_assignments
        else:
            role_assignments = RoleAssignment.objects.filter(
                group=group,
                scope_id=scope.id,
                scope_type=ContentType.objects.get_for_model(scope),
            )
            return list(role_assignments)

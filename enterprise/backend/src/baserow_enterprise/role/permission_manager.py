from collections import defaultdict
from functools import cmp_to_key
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType

from baserow_premium.license.handler import LicenseHandler
from rest_framework.exceptions import NotAuthenticated

from baserow.core.exceptions import PermissionDenied
from baserow.core.models import Group, GroupUser, Operation
from baserow.core.registries import (
    PermissionManagerType,
    object_scope_type_registry,
    operation_type_registry,
)
from baserow_enterprise.features import RBAC
from baserow_enterprise.role.handler import RoleAssignmentHandler

from .models import RoleAssignment

User = get_user_model()


def compare_scopes(a, b):
    a_includes_b = object_scope_type_registry.scope_includes_scope(a.scope, b.scope)
    b_includes_a = object_scope_type_registry.scope_includes_scope(b.scope, a.scope)

    if a_includes_b and b_includes_a:
        return 0
    if a_includes_b:
        return -1
    if b_includes_a:
        return 1


class OperationPermissionContent(TypedDict):
    default: bool
    exceptions: List[int]


class RolePermissionManagerType(PermissionManagerType):
    type = "role"
    _role_cache: Dict[int, List[str]] = {}

    def is_enabled(self, group: Group):
        """
        Checks whether this permission manager should be enabled or not for a
        particular group.

        :param group: The group in which we want to use this permission manager.
        """

        return LicenseHandler.group_has_feature(RBAC, group)

    def get_user_role_assignments(
        self, group: Group, actor: AbstractUser, operation: Optional[Operation] = None
    ) -> List[Tuple[int, Any]]:
        """
        Returns the RoleAssignments for the given actor in the given group.

        :param group: The group the RoleAssignments belong to.
        :param actor: The subject for whom we want the RoleAssignments
        :param operation: An optional Operation to select only roles containing this
            operation.
        :return: A list of tuple containing the role_id and the scope ordered by scope.
            The higher a scope is high in the object hierarchy, the higher the tuple in
            the list.
        """

        roles = RoleAssignment.objects.filter(
            group=group,
            subject_type=ContentType.objects.get_for_model(User),
            subject_id=actor.id,
        )

        if operation:
            roles.filter(role__operations__name=operation.type)

        result = list(roles)

        # TODO performance issue here when getting the scopes.
        # Roles are ordered by scope size. The higher in the hierarchy, the higher
        # in the list.
        result.sort(key=cmp_to_key(compare_scopes))

        # Get the group level role by reading the GroupUser permissions property
        group_level_role = RoleAssignmentHandler().get_role(
            GroupUser.objects.get(user__id=actor.id, group=group).permissions
        )

        if not operation or operation.type in self.get_role_operations(
            group_level_role.id
        ):
            return [
                (
                    group_level_role.id,
                    group,
                )
            ] + [(r.role_id, r.scope) for r in result]

        return [(r.role_id, r.scope) for r in result]

    def get_role_operations(self, role_id: int):
        """
        Return the operation list for the role with the given role_id. This method is
        memoized.

        :param role_id: The role ID we want the operations for.
        """

        if role_id not in self._role_cache:
            self._role_cache[role_id] = Operation.objects.filter(
                roles=role_id
            ).values_list("name", flat=True)

        return self._role_cache[role_id]

    def check_permissions(
        self,
        actor: AbstractUser,
        operation_name: str,
        group: Optional[Group] = None,
        context: Optional[Any] = None,
        include_trash: bool = False,
    ):
        """
        Checks the permission given the role assigned to the actor.
        """

        if group is None or not self.is_enabled(group):
            return

        if hasattr(actor, "is_authenticated"):

            user = actor
            if not user.is_authenticated:
                raise NotAuthenticated()

            if include_trash:
                manager = GroupUser.objects_and_trash
            else:
                manager = GroupUser.objects

            if "ADMIN" in manager.get(user_id=user.id, group_id=group.id).permissions:
                return True

            operation_type = operation_type_registry.get(operation_name)

            # Get all role assignments for this user into this group
            role_assignments = self.get_user_role_assignments(
                group, user, operation=operation_type
            )

            most_precise_role = None

            for (role_id, scope) in role_assignments:
                # Check if this scope include the context. As the role assignments are
                # Sorted, the new scope is more precise than the previous one. So
                # we keep this new role.
                if object_scope_type_registry.scope_includes_context(scope, context):
                    most_precise_role = role_id

            if most_precise_role:
                final_role = self.get_role_operations(most_precise_role)

                if operation_type.type in final_role:
                    return True

            raise PermissionDenied()

    # Probably needs a cache?
    def get_permissions_object(
        self, actor: AbstractUser, group: Optional[Group] = None
    ) -> List[Dict[str, OperationPermissionContent]]:
        """
        Returns the permission object for this permission manager. The permission object
        looks like this:
        ```
        {
            "operation_name1": {"default": True, "exceptions": [3, 5]},
            "operation_name2": {"default": False, "exceptions": [12, 18]},
            ...
        }
        ```
        where `permission_name1` is the name of an operation and for each operation, if
        the operation is permitted by default or not and `exceptions` contains the list
        of context IDs that are an exception to the default rule.
        """

        if group is None or not self.is_enabled(group):
            return None

        # Get all role assignments for this actor into this group
        role_assignments = self.get_user_role_assignments(group, actor)

        result = defaultdict(lambda: {"default": False, "exceptions": set()})

        for (role_id, scope) in role_assignments:

            role = self.get_role_operations(role_id)

            scope_type = object_scope_type_registry.get_by_model(scope)

            # Base permission
            if scope_type.type == "group":
                for operation_name in role:
                    result[operation_name]["default"] = True
                continue

            # Add exceptions for missing operation for this role
            for operation_name, value in result.items():
                if operation_name not in role and value["default"] is True:
                    operation_type = operation_type_registry.get(operation_name)
                    context_ids = [
                        o.id
                        for o in operation_type.context_scope.get_all_context_objects_in_scope(
                            scope
                        )
                    ]
                    value["exceptions"] |= set(context_ids)

            # Check if we need to add exception for operation in this role
            for operation_name in role:

                operation_type = operation_type_registry.get(operation_name)
                context_ids = [
                    o.id
                    for o in operation_type.context_scope.get_all_context_objects_in_scope(
                        scope
                    )
                ]
                # is it an exception?
                if not result[operation_name]["default"]:
                    result[operation_name]["exceptions"] |= set(context_ids)
                else:
                    # We need to remove these ids from the exceptions list if
                    # necessary
                    result[operation_name]["exceptions"] = result[operation_name][
                        "exceptions"
                    ].difference(context_ids)

        return result

    def filter_queryset(
        self, actor, operation_name, queryset, group=None, context=None
    ):
        """
        Filter the given queryset according the role given for the specified operation.
        """

        if group is None or not self.is_enabled(group):
            return queryset

        # Get all role assignments for this user into this group
        role_assignments = self.get_user_role_assignments(group, actor)

        default = False
        exceptions = set([])

        operation_type = operation_type_registry.get(operation_name)

        for (role_id, scope) in role_assignments:

            # Keeps only parents of the current context or children that match the
            # operation object_scope
            if (
                object_scope_type_registry.scope_includes_context(scope, context)
                or object_scope_type_registry.scope_includes_scope(
                    scope, operation_type.object_scope
                )
                and object_scope_type_registry.scope_includes_context(context, scope)
            ):
                role = self.get_role_operations(role_id)

                scope_type = object_scope_type_registry.get_by_model(scope)

                # Base permission
                if scope_type.type == "group" and operation_name in role:
                    default = True
                    continue

                context_ids = [
                    o.id
                    for o in operation_type.object_scope.get_all_context_objects_in_scope(
                        scope
                    )
                ]
                # Remove or add exceptions to the exceptions list
                if operation_name not in role:
                    if default:
                        exceptions |= set(context_ids)
                    else:
                        exceptions = exceptions.difference(context_ids)
                else:
                    if default:
                        exceptions = exceptions.difference(context_ids)
                    else:
                        exceptions |= set(context_ids)

        # Finally filter the query set with the exception list.
        if default:
            queryset = queryset.exclude(id__in=list(exceptions))
        else:
            queryset = queryset.filter(id__in=list(exceptions))

        return queryset

from collections import defaultdict
from functools import cached_property
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

from baserow_premium.license.handler import LicenseHandler
from rest_framework.exceptions import NotAuthenticated

from baserow.core.exceptions import PermissionDenied
from baserow.core.models import Group
from baserow.core.registries import (
    OperationType,
    PermissionManagerType,
    object_scope_type_registry,
    operation_type_registry,
)
from baserow_enterprise.features import RBAC
from baserow_enterprise.role.handler import RoleAssignmentHandler

from .models import Role

User = get_user_model()


class OperationPermissionContent(TypedDict):
    default: bool
    exceptions: List[int]


class RolePermissionManagerType(PermissionManagerType):
    type = "role"

    def is_enabled(self, group: Group):
        """
        Checks whether this permission manager should be enabled or not for a
        particular group.

        :param group: The group in which we want to use this permission manager.
        """

        return LicenseHandler.group_has_feature(RBAC, group)

    def get_role_operations(self, role: Role) -> List[str]:
        """
        Return the operation name list for the role with the given role_id.

        :param role: The role we want the operation names for.
        :return: A list of role operation name.
        """

        return set([op.name for op in role.operations.all()])

    @cached_property
    def read_operations(self) -> Set[str]:
        """
        Return the read operation list.
        """

        return set(
            op.name
            for op in RoleAssignmentHandler().get_role_by_uid("VIEWER").operations.all()
        )

    def check_permissions(
        self,
        actor: AbstractUser,
        operation_name: str,
        group: Optional[Group] = None,
        context: Optional[Any] = None,
        include_trash: bool = False,
    ):
        """
        Checks the permissions given the roles assigned to the actor.
        """

        if group is None or not self.is_enabled(group):
            return

        if hasattr(actor, "is_authenticated"):

            user = actor
            if not user.is_authenticated:
                raise NotAuthenticated()

            operation_type = operation_type_registry.get(operation_name)

            computed_roles = RoleAssignmentHandler().get_computed_roles(
                group, actor, context
            )

            if any(
                [
                    operation_type.type in self.get_role_operations(r)
                    for r in computed_roles
                ]
            ):
                return True

            raise PermissionDenied()

    def get_operation_policy(
        self,
        roles_by_scope: List[Tuple[Any, List[Role]]],
        operation_type: OperationType,
        use_object_scope: bool = False,
    ) -> Tuple[bool, Set[Any]]:
        """
        Compute the default policy and exceptions for an operation given the
        role assignments.

        :param role_assignments: The role assignments used to compute the policy.
        :param operation_type: The operation type we want the policy for.
        :param use_object_scope: Use the `object_scope` instead of the `context_scope`
            of the scope_type. This change the type of returned objects.
        :return: A tuple. The first element is the default policy. The second element
            is a set of context or object that are exceptions to the default policy.
        """

        base_scope_type = (
            operation_type.object_scope
            if use_object_scope
            else operation_type.context_scope
        )

        # Default permissions at the group level
        _, default_group_roles = roles_by_scope[0]
        default = any(
            [
                operation_type.type in self.get_role_operations(r)
                for r in default_group_roles
            ]
        )
        exceptions = set()

        for (scope, roles) in roles_by_scope[1:]:

            allowed_operations = set()
            [
                allowed_operations.update(self.get_role_operations(role))
                for role in roles
            ]

            scope_type = object_scope_type_registry.get_by_model(scope)

            # First case
            # The scope of the role assignment includes the scope of the operation
            # So it has an influence on the result
            if object_scope_type_registry.scope_type_includes_scope_type(
                scope_type, base_scope_type
            ):

                context_exceptions = list(
                    base_scope_type.get_all_context_objects_in_scope(scope)
                )

                # Remove or add exceptions to the exception list according to the
                # default policy for the group
                if operation_type.type not in allowed_operations:
                    if default:
                        exceptions |= set(context_exceptions)
                    else:
                        exceptions = exceptions.difference(context_exceptions)
                else:
                    if default:
                        exceptions = exceptions.difference(context_exceptions)
                    else:
                        exceptions |= set(context_exceptions)
            # Second case
            # The scope of the role assignment is included by the role of the operation
            # And we are doing a read operation
            # So we must enable the read operation for the parent
            elif (
                operation_type.type in self.read_operations
                and allowed_operations
                and object_scope_type_registry.scope_type_includes_scope_type(
                    base_scope_type, scope_type
                )
            ):
                # - It's a read operation and
                # - we have a children that have at least one allowed operation
                # -> we should then allow all read operations for any ancestor of
                # this scope object.
                found_object = object_scope_type_registry.get_parent(
                    scope, at_scope_type=base_scope_type
                )

                if default:
                    if found_object in exceptions:
                        exceptions.remove(found_object)
                else:
                    exceptions.add(found_object)

        return default, exceptions

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
        roles_by_scope = RoleAssignmentHandler().get_roles_per_scope(group, actor)

        result = defaultdict(lambda: {"default": False, "exceptions": []})

        for operation_type in operation_type_registry.get_all():

            default, exceptions = self.get_operation_policy(
                roles_by_scope, operation_type
            )

            if default or exceptions:
                result[operation_type.type]["default"] = default
                result[operation_type.type]["exceptions"] = [e.id for e in exceptions]

        return result

    def filter_queryset(
        self, actor, operation_name, queryset, group=None, context=None
    ):
        """
        Filter the given queryset according to the role given for the specified
        operation.
        """

        if group is None or not self.is_enabled(group):
            return queryset

        # Get all role assignments for this user into this group
        roles_by_scope = RoleAssignmentHandler().get_roles_per_scope(group, actor)
        print(roles_by_scope)

        operation_type = operation_type_registry.get(operation_name)

        default, exceptions = self.get_operation_policy(
            roles_by_scope, operation_type, True
        )

        exceptions = [e.id for e in exceptions]

        print(default, exceptions)

        # Finally filter the queryset with the exception list.
        if default:
            if exceptions:
                queryset = queryset.exclude(id__in=list(exceptions))
        else:
            if exceptions:
                queryset = queryset.filter(id__in=list(exceptions))
            else:
                queryset = queryset.none()

        return queryset

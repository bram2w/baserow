from collections import defaultdict
from functools import cached_property
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

from baserow_premium.license.handler import LicenseHandler

from baserow.core.exceptions import PermissionDenied
from baserow.core.models import Group
from baserow.core.registries import (
    OperationType,
    PermissionManagerType,
    object_scope_type_registry,
    operation_type_registry,
    subject_type_registry,
)
from baserow.core.subjects import UserSubjectType
from baserow.core.types import PermissionCheck
from baserow_enterprise.features import RBAC
from baserow_enterprise.role.handler import RoleAssignmentHandler

from .models import Role

User = get_user_model()


class OperationPermissionContent(TypedDict):
    default: bool
    exceptions: List[int]


class RolePermissionManagerType(PermissionManagerType):
    type = "role"
    supported_actor_types = [UserSubjectType.type]

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

    def check_multiple_permissions(
        self, checks: List[PermissionCheck], group=None, include_trash=False
    ):
        """
        Checks the permissions for each check.
        """

        if group is None or not self.is_enabled(group):
            return {}

        # Group actor by subject_type
        actors_by_subject_type = defaultdict(set)
        for actor, _, _ in checks:
            s_type = subject_type_registry.get_by_model(actor)
            actors_by_subject_type[s_type].add(actor)

        result = {}
        scope_includes_cache = {}
        for actor_subject_type, actors in actors_by_subject_type.items():
            computed_role_cache = {}
            roles_per_scope_by_actor = (
                RoleAssignmentHandler().get_roles_per_scope_for_actors(
                    group, actor_subject_type, actors, include_trash=include_trash
                )
            )

            for check in checks:
                actor, operation_name, context = check
                cache_key = (
                    actor.id,
                    f"{type(context).__name__}__{context.id}",
                )
                if cache_key not in computed_role_cache:
                    # Compute the actual role for this check
                    computed_role_cache[
                        cache_key
                    ] = RoleAssignmentHandler().get_computed_roles(
                        roles_per_scope_by_actor[actor],
                        context,
                        scope_includes_cache,
                    )
                computed_roles = computed_role_cache[cache_key]

                if any(
                    [
                        operation_name in self.get_role_operations(r)
                        for r in computed_roles
                    ]
                ):
                    result[check] = True
                else:
                    result[check] = PermissionDenied()

        return result

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

            for role in roles:
                allowed_operations.update(self.get_role_operations(role))

            scope_type = object_scope_type_registry.get_by_model(scope)

            # First case
            # The scope of the role assignment includes the scope of the operation
            # So it has an influence on the result
            if object_scope_type_registry.scope_type_includes_scope_type(
                scope_type, base_scope_type
            ):

                context_exception = scope
                # Remove or add exceptions to the exception list according to the
                # default policy for the group
                if operation_type.type not in allowed_operations:
                    if default:
                        exceptions.add(context_exception)
                    else:
                        exceptions.discard(context_exception)
                else:
                    if default:
                        exceptions.discard(context_exception)
                    else:
                        exceptions.add(context_exception)

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
                        exceptions.discard(found_object)
                else:
                    exceptions.add(found_object)

        return default, exceptions

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

        policy_per_operation = defaultdict(lambda: {"default": False, "exceptions": []})

        exceptions_with_mixed_types_per_scope = defaultdict(set)

        # First, for each operation we want the default policy and exceptions
        for operation_type in operation_type_registry.get_all():
            default, exceptions = self.get_operation_policy(
                roles_by_scope, operation_type
            )

            if default or exceptions:
                policy_per_operation[operation_type.type]["default"] = default
                policy_per_operation[operation_type.type]["exceptions"] = exceptions

            if exceptions:
                # We store the exceptions by scope to get all objects at once later
                exceptions_with_mixed_types_per_scope[
                    operation_type.context_scope
                ] |= exceptions

        # Get all objects for all exceptions at once to improve perfs
        exception_ids_per_scope = {}
        for object_scope, exceptions in exceptions_with_mixed_types_per_scope.items():
            exception_ids_per_scope[object_scope] = {
                scope: {o.id for o in exc}
                for scope, exc in object_scope.get_objects_in_scopes(exceptions).items()
            }

        # Dispatch actual context object ids for each exceptions scopes
        policy_per_operation_with_exception_ids = {}
        for operation_type in operation_type_registry.get_all():

            # Gather all ids for all scopes of the exception list of this operation
            exceptions_ids = set()
            for scope in policy_per_operation[operation_type.type]["exceptions"]:
                exceptions_ids |= exception_ids_per_scope[operation_type.context_scope][
                    scope
                ]

            policy_per_operation_with_exception_ids[operation_type.type] = {
                "default": policy_per_operation[operation_type.type]["default"],
                "exceptions": list(exceptions_ids),
            }

        return policy_per_operation_with_exception_ids

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
        operation_type = operation_type_registry.get(operation_name)

        default, exceptions = self.get_operation_policy(
            roles_by_scope, operation_type, True
        )

        exceptions_filter = operation_type.object_scope.get_filter_for_scopes(
            exceptions
        )

        # Finally filter the queryset with the exception filter.
        if default:
            if exceptions:
                queryset = queryset.exclude(exceptions_filter)
        else:
            if exceptions:
                queryset = queryset.filter(exceptions_filter)
            else:
                queryset = queryset.none()

        return queryset

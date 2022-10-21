from collections import defaultdict
from functools import cached_property, cmp_to_key
from typing import Dict, List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from rest_framework.exceptions import NotAuthenticated

from baserow.core.exceptions import PermissionDenied, UserNotInGroup
from baserow.core.models import GroupUser
from baserow.core.registries import (
    PermissionManagerType,
    object_scope_type_registry,
    operation_type_registry,
)

from .models import Role, RoleAssignment

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


class RolePermissionManagerType(PermissionManagerType):
    type = "role"
    _role_cache: Dict[int, List[str]] = {}

    def is_enabled(self, group):
        return "roles" in settings.FEATURE_FLAGS

    @cached_property
    def user_subject_type(self):
        return ContentType.objects.get_for_model(User)

    def get_user_role_assignments(self, group, actor, operation=None):
        roles = RoleAssignment.objects.filter(
            group=group, subject_type=self.user_subject_type, subject_id=actor.id
        )
        if operation:
            roles.filter(role__operations=operation)

        result = list(roles)

        # Roles are ordered by scope size. The higher in the hierarchy, the higher
        # in the list.
        result.sort(key=cmp_to_key(compare_scopes))
        return [(r.role_id, r.scope) for r in result]

    def get_role(self, role_id):
        if role_id not in self._role_cache:
            role = Role.objects.get(id=role_id)
            self._role_cache[role_id] = [p.name for p in role.operations.all()]

        return self._role_cache[role_id]

    def check_permissions(
        self, actor, operation, group=None, context=None, include_trash=False
    ):

        if group is None:
            return

        if not self.is_enabled(group):
            return

        if hasattr(actor, "is_authenticated"):

            user = actor
            if not user.is_authenticated:
                raise NotAuthenticated()

            if include_trash:
                manager = GroupUser.objects_and_trash
            else:
                manager = GroupUser.objects

            try:
                if (
                    "ADMIN"
                    in manager.get(user_id=user.id, group_id=group.id).permissions
                ):
                    return True
            except GroupUser.DoesNotExist:
                raise UserNotInGroup(user, self)

            # Get all role assignments for this group
            role_assignments = self.get_user_role_assignments(group, actor)

            most_precise_role = None

            operation_type = operation_type_registry.get(operation)

            for (role_id, scope) in role_assignments:
                # Keeps only scope that are parents of the current context
                if object_scope_type_registry.scope_includes_context(scope, context):
                    most_precise_role = role_id

            if most_precise_role:
                final_role = self.get_role(most_precise_role)

                if operation_type.type in final_role:
                    return True

            raise PermissionDenied()

    # Probably needs a cache?
    def get_permissions_object(self, actor, group=None):

        if group is None:
            return None

        if not self.is_enabled(group):
            return

        # Get all role assignments for this group
        role_assignments = self.get_user_role_assignments(group, actor)

        result = defaultdict(lambda: {"default": False, "exceptions": set()})

        for (role_id, scope) in role_assignments:

            role = self.get_role(role_id)

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

        if group is None:
            return queryset

        if not self.is_enabled(group):
            return queryset

        # Get all role assignments for this group
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
                role = self.get_role(role_id)

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

        if default:
            queryset = queryset.exclude(id__in=list(exceptions))
        else:
            queryset = queryset.filter(id__in=list(exceptions))

        return queryset

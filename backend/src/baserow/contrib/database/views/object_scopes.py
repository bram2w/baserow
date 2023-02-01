from django.db.models import Q

from baserow.contrib.database.object_scopes import DatabaseObjectScopeType
from baserow.contrib.database.table.object_scopes import DatabaseTableObjectScopeType
from baserow.contrib.database.views.models import (
    View,
    ViewDecoration,
    ViewFilter,
    ViewSort,
)
from baserow.core.object_scopes import ApplicationObjectScopeType, GroupObjectScopeType
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class DatabaseViewObjectScopeType(ObjectScopeType):

    type = "database_view"
    model_class = View

    def get_parent_scope(self):
        return object_scope_type_registry.get("database_table")

    def get_parent(self, context):
        return context.table

    def get_enhanced_queryset(self):
        return self.get_base_queryset().prefetch_related(
            "table", "table__database", "table__database__group"
        )

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(table__database__group__in=[s.id for s in scopes])

        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return Q(table__database__in=[s.id for s in scopes])

        if scope_type.type == DatabaseTableObjectScopeType.type:
            return Q(table__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")


class DatabaseViewDecorationObjectScopeType(ObjectScopeType):

    type = "database_view_decoration"
    model_class = ViewDecoration

    def get_parent_scope(self):
        return object_scope_type_registry.get("database_view")

    def get_parent(self, context):
        return context.view

    def get_enhanced_queryset(self):
        return self.get_base_queryset().prefetch_related(
            "view",
            "view__table",
            "view__table__database",
            "view__table__database__group",
        )

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(view_table__database__group__in=[s.id for s in scopes])

        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return Q(view__table__database__in=[s.id for s in scopes])

        if scope_type.type == DatabaseTableObjectScopeType.type:
            return Q(view__table__in=[s.id for s in scopes])

        if scope_type.type == DatabaseViewObjectScopeType.type:
            return Q(view__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")


class DatabaseViewSortObjectScopeType(ObjectScopeType):

    type = "database_view_sort"
    model_class = ViewSort

    def get_parent_scope(self):
        return object_scope_type_registry.get("database_view")

    def get_parent(self, context):
        return context.view

    def get_enhanced_queryset(self):
        return self.get_base_queryset().prefetch_related(
            "view",
            "view__table",
            "view__table__database",
            "view__table__database__group",
        )

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(view_table__database__group__in=[s.id for s in scopes])

        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return Q(view__table__database__in=[s.id for s in scopes])

        if scope_type.type == DatabaseTableObjectScopeType.type:
            return Q(view__table__in=[s.id for s in scopes])

        if scope_type.type == DatabaseViewObjectScopeType.type:
            return Q(view__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")


class DatabaseViewFilterObjectScopeType(ObjectScopeType):

    type = "database_view_filter"
    model_class = ViewFilter

    def get_parent_scope(self):
        return object_scope_type_registry.get("database_view")

    def get_parent(self, context):
        return context.view

    def get_enhanced_queryset(self):
        return self.get_base_queryset().prefetch_related(
            "view",
            "view__table",
            "view__table__database",
            "view__table__database__group",
        )

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(view_table__database__group__in=[s.id for s in scopes])

        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return Q(view__table__database__in=[s.id for s in scopes])

        if scope_type.type == DatabaseTableObjectScopeType.type:
            return Q(view__table__in=[s.id for s in scopes])

        if scope_type.type == DatabaseViewObjectScopeType.type:
            return Q(view__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")

from typing import Iterable

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
from baserow.core.types import ScopeObject


class DatabaseViewObjectScopeType(ObjectScopeType):

    type = "database_view"
    model_class = View

    def get_parent_scope(self):
        return object_scope_type_registry.get("database_table")

    def get_parent(self, context):
        return context.table

    def get_all_context_objects_in_scope(self, scope: ScopeObject) -> Iterable:
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == GroupObjectScopeType.type:
            return View.objects.filter(table__database__group=scope.id)
        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return View.objects.filter(table__database=scope.id)
        if scope_type.type == DatabaseTableObjectScopeType.type:
            return View.objects.filter(table=scope.id)
        if scope_type.type == self.type:
            return [scope]
        return []


class DatabaseViewDecorationObjectScopeType(ObjectScopeType):

    type = "database_view_decoration"
    model_class = ViewDecoration

    def get_parent_scope(self):
        return object_scope_type_registry.get("database_view")

    def get_parent(self, context):
        return context.view

    def get_all_context_objects_in_scope(self, scope: ScopeObject) -> Iterable:
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == GroupObjectScopeType.type:
            return ViewDecoration.objects.filter(view__table__database__group=scope.id)
        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return ViewDecoration.objects.filter(view__table__database=scope.id)
        if scope_type.type == DatabaseTableObjectScopeType.type:
            return ViewDecoration.objects.filter(view__table=scope.id)
        if scope_type.type == DatabaseViewObjectScopeType.type:
            return ViewDecoration.objects.filter(view=scope.id)
        if scope_type.type == self.type:
            return [scope]
        return []


class DatabaseViewSortObjectScopeType(ObjectScopeType):

    type = "database_view_sort"
    model_class = ViewSort

    def get_parent_scope(self):
        return object_scope_type_registry.get("database_view")

    def get_parent(self, context):
        return context.view

    def get_all_context_objects_in_scope(self, scope: ScopeObject) -> Iterable:
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == GroupObjectScopeType.type:
            return ViewSort.objects.filter(view__table__database__group=scope.id)
        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return ViewSort.objects.filter(view__table__database=scope.id)
        if scope_type.type == DatabaseTableObjectScopeType.type:
            return ViewSort.objects.filter(view__table=scope.id)
        if scope_type.type == DatabaseViewObjectScopeType.type:
            return ViewSort.objects.filter(view=scope.id)
        if scope_type.type == self.type:
            return [scope]
        return []


class DatabaseViewFilterObjectScopeType(ObjectScopeType):

    type = "database_view_filter"
    model_class = ViewFilter

    def get_parent_scope(self):
        return object_scope_type_registry.get("database_view")

    def get_parent(self, context):
        return context.view

    def get_all_context_objects_in_scope(self, scope: ScopeObject) -> Iterable:
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == GroupObjectScopeType.type:
            return ViewFilter.objects.filter(view__table__database__group=scope.id)
        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return ViewFilter.objects.filter(view__table__database=scope.id)
        if scope_type.type == DatabaseTableObjectScopeType.type:
            return ViewFilter.objects.filter(view__table=scope.id)
        if scope_type.type == DatabaseViewObjectScopeType.type:
            return ViewFilter.objects.filter(view=scope.id)
        if scope_type.type == self.type:
            return [scope]
        return []

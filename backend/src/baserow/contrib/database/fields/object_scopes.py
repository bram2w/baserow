from django.db.models import Q, QuerySet

from baserow.contrib.database.models import Field
from baserow.contrib.database.object_scopes import DatabaseObjectScopeType
from baserow.contrib.database.table.object_scopes import DatabaseTableObjectScopeType
from baserow.core.object_scopes import (
    ApplicationObjectScopeType,
    WorkspaceObjectScopeType,
)
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class FieldObjectScopeType(ObjectScopeType):
    type = "database_field"
    model_class = Field

    def get_parent_scope(self):
        return object_scope_type_registry.get("database_table")

    def get_base_queryset(self, include_trash: bool = False) -> QuerySet:
        return (
            super()
            .get_base_queryset(include_trash)
            .filter(
                table__database__workspace__isnull=False,
            )
        )

    def get_enhanced_queryset(self, include_trash: bool = False):
        return self.get_base_queryset(include_trash).select_related(
            "table__database__workspace"
        )

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == WorkspaceObjectScopeType.type:
            return Q(table__database__workspace__in=[s.id for s in scopes])

        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return Q(table__database__in=[s.id for s in scopes])

        if scope_type.type == DatabaseTableObjectScopeType.type:
            return Q(table__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")

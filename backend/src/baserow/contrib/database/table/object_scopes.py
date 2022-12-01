from baserow.contrib.database.object_scopes import DatabaseObjectScopeType
from baserow.contrib.database.table.models import Table
from baserow.core.object_scopes import ApplicationObjectScopeType, GroupObjectScopeType
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class DatabaseTableObjectScopeType(ObjectScopeType):
    type = "database_table"
    model_class = Table

    def get_parent_scope(self):
        return object_scope_type_registry.get("database")

    def get_parent(self, context):
        return context.database

    def get_all_context_objects_in_scope(self, scope):
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == GroupObjectScopeType.type:
            return Table.objects.filter(database__group=scope.id)
        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return Table.objects.filter(database=scope.id)
        if scope_type.type == DatabaseTableObjectScopeType.type:
            return [scope]
        return []

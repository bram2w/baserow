from baserow.contrib.database.models import Field
from baserow.contrib.database.object_scopes import DatabaseObjectScopeType
from baserow.contrib.database.table.object_scopes import DatabaseTableObjectScopeType
from baserow.core.object_scopes import ApplicationObjectScopeType, GroupObjectScopeType
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class FieldObjectScopeType(ObjectScopeType):
    type = "database_field"
    model_class = Field

    def get_parent_scope(self):
        return object_scope_type_registry.get("database_table")

    def get_parent(self, context):
        return context.table

    def get_all_context_objects_in_scope(self, scope):
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == GroupObjectScopeType.type:
            return Field.objects.filter(table__database__group=scope)
        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return Field.objects.filter(table__database=scope)
        if scope_type.type == DatabaseTableObjectScopeType.type:
            return Field.objects.filter(table=scope)
        if scope_type.type == FieldObjectScopeType.type:
            return [scope]
        return []

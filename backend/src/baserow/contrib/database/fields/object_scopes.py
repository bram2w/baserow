from baserow.contrib.database.models import Field
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class FieldObjectScopeType(ObjectScopeType):
    type = "field"
    model_class = Field

    def get_parent_scope(self):
        return object_scope_type_registry.get("table")

    def get_parent(self, context):
        return context.table

    def get_all_context_objects_in_scope(self, scope):
        if object_scope_type_registry.get_by_model(scope).type == "group":
            return Field.objects.filter(table__database__group=scope)
        if object_scope_type_registry.get_by_model(scope).type == "database":
            return Field.objects.filter(table__database=scope)
        if object_scope_type_registry.get_by_model(scope).type == "table":
            return Field.objects.filter(table=scope)
        if object_scope_type_registry.get_by_model(scope).type == "field":
            return [scope]
        return []

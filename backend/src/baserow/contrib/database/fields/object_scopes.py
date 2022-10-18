from baserow.contrib.database.models import Field
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class FieldObjectScopeType(ObjectScopeType):
    type = "field"
    model_class = Field

    def get_parent_scope(self):
        return object_scope_type_registry.get("table")

    def get_parent(self, context):
        return context.table

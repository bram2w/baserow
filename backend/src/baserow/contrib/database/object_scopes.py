from baserow.contrib.database.models import Database
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class DatabaseObjectScopeType(ObjectScopeType):
    type = "database"
    model_class = Database

    def get_parent_scope(self):
        return object_scope_type_registry.get("group")

    def get_parent(self, context):
        return context.group

    def get_all_context_objects_in_scope(self, scope):
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == "group":
            return Database.objects.filter(group=scope)
        if scope_type.type == "database":
            return [scope]

        return []

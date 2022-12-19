from baserow.contrib.database.models import Database
from baserow.core.object_scopes import ApplicationObjectScopeType, GroupObjectScopeType
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class DatabaseObjectScopeType(ObjectScopeType):
    type = "database"
    model_class = Database

    def get_parent_scope(self):
        return object_scope_type_registry.get("application")

    def get_parent(self, context):
        # Parent is the Application here even if it's at the "same" level
        # but it's a more generic type
        return context.application_ptr

    def get_all_context_objects_in_scope(self, scope):
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == GroupObjectScopeType.type:
            return Database.objects.filter(group=scope)
        if (
            scope_type.type == DatabaseObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return [scope]

        return []

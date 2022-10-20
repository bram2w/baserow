from baserow.core.models import Snapshot
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class SnapshotObjectScopeType(ObjectScopeType):
    type = "snapshot"
    model_class = Snapshot

    def get_parent_scope(self):
        return object_scope_type_registry.get("application")

    def get_parent(self, context):
        return context.snapshot_from_application.specific

    def get_all_context_objects_in_scope(self, scope):
        if object_scope_type_registry.get_by_model(scope).type == "group":
            return Snapshot.objects.filter(group=scope)
        if object_scope_type_registry.get_by_model(scope).type == "snapshot":
            return [scope]
        return []

from baserow.core.models import Snapshot
from baserow.core.object_scopes import ApplicationObjectScopeType, GroupObjectScopeType
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class SnapshotObjectScopeType(ObjectScopeType):
    type = "snapshot"
    model_class = Snapshot

    def get_parent_scope(self):
        return object_scope_type_registry.get("application")

    def get_parent(self, context):
        return context.snapshot_from_application.specific

    def get_all_context_objects_in_scope(self, scope):
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == GroupObjectScopeType.type:
            return Snapshot.objects.filter(snapshot_from_application__group=scope)
        if scope_type.type == ApplicationObjectScopeType.type:
            return Snapshot.objects.filter(snapshot_from_application=scope)
        if scope_type.type == self.type:
            return [scope]
        return []

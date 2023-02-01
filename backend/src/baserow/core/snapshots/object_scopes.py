from django.db.models import Q

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

    def get_enhanced_queryset(self):
        return self.get_base_queryset().prefetch_related(
            "snapshot_from_application", "snapshot_from_application__group"
        )

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(snapshot_from_application__group__in=[s.id for s in scopes])

        if scope_type.type == ApplicationObjectScopeType.type:
            return Q(snapshot_from_application__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")

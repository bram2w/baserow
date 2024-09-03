from django.db.models import Q, QuerySet

from baserow.core.models import Snapshot
from baserow.core.object_scopes import (
    ApplicationObjectScopeType,
    WorkspaceObjectScopeType,
)
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class SnapshotObjectScopeType(ObjectScopeType):
    type = "snapshot"
    model_class = Snapshot

    def get_parent_scope(self):
        return object_scope_type_registry.get("application")

    def get_enhanced_queryset(self, include_trash: bool = False) -> QuerySet:
        return self.get_base_queryset(include_trash).select_related(
            "snapshot_from_application__workspace"
        )

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == WorkspaceObjectScopeType.type:
            return Q(snapshot_from_application__workspace__in=[s.id for s in scopes])

        if scope_type.type == ApplicationObjectScopeType.type:
            return Q(snapshot_from_application__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")

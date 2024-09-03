from typing import Optional

from django.db.models import Q, QuerySet

from baserow.contrib.builder.domains.models import Domain
from baserow.contrib.builder.object_scopes import BuilderObjectScopeType
from baserow.core.object_scopes import (
    ApplicationObjectScopeType,
    WorkspaceObjectScopeType,
)
from baserow.core.registries import ObjectScopeType, object_scope_type_registry
from baserow.core.types import ContextObject


class BuilderDomainObjectScopeType(ObjectScopeType):
    type = "builder_domain"
    model_class = Domain

    def get_parent_scope(self) -> Optional["ObjectScopeType"]:
        return object_scope_type_registry.get("builder")

    def get_parent(self, context: ContextObject) -> Optional[ContextObject]:
        return context.builder

    def get_base_queryset(self, include_trash: bool = False) -> QuerySet:
        return (
            super()
            .get_base_queryset(include_trash)
            .filter(builder__workspace__isnull=False)
        )

    def get_enhanced_queryset(self, include_trash: bool = False) -> QuerySet:
        return self.get_base_queryset(include_trash).select_related(
            "builder__workspace"
        )

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == WorkspaceObjectScopeType.type:
            return Q(builder__workspace__in=[s.id for s in scopes])

        if (
            scope_type.type == BuilderObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return Q(builder__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")

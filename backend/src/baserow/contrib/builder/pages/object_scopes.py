from typing import Optional

from django.db.models import Q, QuerySet

from baserow.contrib.builder.object_scopes import BuilderObjectScopeType
from baserow.contrib.builder.pages.models import Page
from baserow.core.object_scopes import (
    ApplicationObjectScopeType,
    WorkspaceObjectScopeType,
)
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class BuilderPageObjectScopeType(ObjectScopeType):
    type = "builder_page"
    model_class = Page

    def get_parent_scope(self) -> Optional["ObjectScopeType"]:
        return object_scope_type_registry.get("builder")

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

from typing import Optional

from django.db.models import Q

from baserow.contrib.builder.object_scopes import BuilderObjectScopeType
from baserow.contrib.builder.pages.models import Page
from baserow.core.object_scopes import ApplicationObjectScopeType, GroupObjectScopeType
from baserow.core.registries import ObjectScopeType, object_scope_type_registry
from baserow.core.types import ContextObject


class BuilderPageObjectScopeType(ObjectScopeType):
    type = "builder_page"
    model_class = Page

    def get_parent_scope(self) -> Optional["ObjectScopeType"]:
        return object_scope_type_registry.get("builder")

    def get_parent(self, context: ContextObject) -> Optional[ContextObject]:
        return context.builder

    def get_enhanced_queryset(self):
        return self.get_base_queryset().prefetch_related("builder", "builder__group")

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(builder__group__in=[s.id for s in scopes])

        if (
            scope_type.type == BuilderObjectScopeType.type
            or scope_type.type == ApplicationObjectScopeType.type
        ):
            return Q(builder__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")

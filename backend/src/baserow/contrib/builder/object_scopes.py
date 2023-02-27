from django.db.models import Q

from baserow.contrib.builder.models import Builder
from baserow.core.object_scopes import ApplicationObjectScopeType, GroupObjectScopeType
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class BuilderObjectScopeType(ObjectScopeType):
    type = "builder"
    model_class = Builder

    def get_parent_scope(self):
        return object_scope_type_registry.get("application")

    def get_parent(self, context):
        # Parent is the Application here even if it's at the "same" level
        # but it's a more generic type
        return context.application_ptr

    def get_enhanced_queryset(self):
        return self.get_base_queryset().prefetch_related("group")

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == GroupObjectScopeType.type:
            return Q(group__in=[s.id for s in scopes])
        if scope_type.type == ApplicationObjectScopeType.type:
            return Q(id__in=[s.id for s in scopes])
        if scope_type.type == self.type:
            return Q(id__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")

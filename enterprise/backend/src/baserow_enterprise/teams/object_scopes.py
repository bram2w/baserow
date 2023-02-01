from django.db.models import Q

from baserow.core.object_scopes import GroupObjectScopeType
from baserow.core.registries import ObjectScopeType, object_scope_type_registry
from baserow_enterprise.models import Team, TeamSubject


class TeamObjectScopeType(ObjectScopeType):
    type = "team"
    model_class = Team

    def get_parent_scope(self):
        return object_scope_type_registry.get("group")

    def get_parent(self, context):
        return context.group

    def get_enhanced_queryset(self):
        return self.get_base_queryset().prefetch_related("group")

    def get_filter_for_scope_type(self, scope_type, scopes):

        if scope_type.type == GroupObjectScopeType.type:
            return Q(group__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")


class TeamSubjectObjectScopeType(ObjectScopeType):
    type = "team_subject"
    model_class = TeamSubject

    def get_parent_scope(self):
        return object_scope_type_registry.get("team")

    def get_parent(self, context):
        return context.team

    def get_enhanced_queryset(self):
        return self.get_base_queryset().prefetch_related("team", "team__group")

    def get_filter_for_scope_type(self, scope_type, scopes):

        if scope_type.type == GroupObjectScopeType.type:
            return Q(team__group__in=[s.id for s in scopes])

        if scope_type.type == TeamObjectScopeType.type:
            return Q(team__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")

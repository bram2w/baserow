from django.db.models import Q, QuerySet

from baserow.core.object_scopes import WorkspaceObjectScopeType
from baserow.core.registries import ObjectScopeType, object_scope_type_registry
from baserow_enterprise.models import Team, TeamSubject


class TeamObjectScopeType(ObjectScopeType):
    type = "team"
    model_class = Team

    def get_parent_scope(self):
        return object_scope_type_registry.get("workspace")

    def get_enhanced_queryset(self, include_trash: bool = False) -> QuerySet:
        return self.get_base_queryset(include_trash).select_related("workspace")

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == WorkspaceObjectScopeType.type:
            return Q(workspace__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")


class TeamSubjectObjectScopeType(ObjectScopeType):
    type = "team_subject"
    model_class = TeamSubject

    def get_parent_scope(self):
        return object_scope_type_registry.get("team")

    def get_enhanced_queryset(self, include_trash: bool = False) -> QuerySet:
        return self.get_base_queryset(include_trash).select_related("team__workspace")

    def get_filter_for_scope_type(self, scope_type, scopes):
        if scope_type.type == WorkspaceObjectScopeType.type:
            return Q(team__workspace__in=[s.id for s in scopes])

        if scope_type.type == TeamObjectScopeType.type:
            return Q(team__in=[s.id for s in scopes])

        raise TypeError("The given type is not handled.")

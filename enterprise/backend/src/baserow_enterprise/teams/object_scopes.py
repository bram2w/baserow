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

    def get_all_context_objects_in_scope(self, scope):
        scope_type = object_scope_type_registry.get_by_model(scope).type
        if scope_type.type == GroupObjectScopeType.type:
            return Team.objects.filter(group=scope)
        if object_scope_type_registry.get_by_model(scope).type == self.type:
            return [scope]
        return []


class TeamSubjectObjectScopeType(ObjectScopeType):
    type = "team_subject"
    model_class = TeamSubject

    def get_parent_scope(self):
        return object_scope_type_registry.get("team")

    def get_parent(self, context):
        return context.team

    def get_all_context_objects_in_scope(self, scope):
        scope_type = object_scope_type_registry.get_by_model(scope).type
        if scope_type.type == GroupObjectScopeType.type:
            return TeamSubject.objects.filter(team__group=scope)
        if scope_type.type == TeamObjectScopeType.type:
            return TeamSubject.objects.filter(team=scope)
        if scope_type.type == self.type:
            return [scope]
        return []

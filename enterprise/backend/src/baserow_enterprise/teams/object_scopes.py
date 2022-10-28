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
        if object_scope_type_registry.get_by_model(scope).type == "team":
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
        if object_scope_type_registry.get_by_model(scope).type == "team_subject":
            return [scope]
        return []

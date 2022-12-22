from baserow.core.models import Application, Group, GroupInvitation, GroupUser
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class CoreObjectScopeType(ObjectScopeType):
    model_class = type(None)
    type = "core"

    def get_all_context_objects_in_scope(self, scope):
        return []


class GroupObjectScopeType(ObjectScopeType):
    type = "group"
    model_class = Group

    def get_all_context_objects_in_scope(self, scope):
        if object_scope_type_registry.get_by_model(scope).type == self.type:
            return [scope]
        return []


class ApplicationObjectScopeType(ObjectScopeType):
    type = "application"
    model_class = Application

    def get_all_context_objects_in_scope(self, scope):
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == GroupObjectScopeType.type:
            return Application.objects.filter(group=scope)
        if scope_type.type == self.type:
            return [scope]
        return []

    def get_parent_scope(self):
        return object_scope_type_registry.get("group")

    def get_parent(self, context):
        return context.group


class GroupInvitationObjectScopeType(ObjectScopeType):
    type = "group_invitation"
    model_class = GroupInvitation

    def get_parent_scope(self):
        return object_scope_type_registry.get("group")

    def get_parent(self, context):
        return context.group

    def get_all_context_objects_in_scope(self, scope):
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == GroupObjectScopeType.type:
            return GroupInvitation.objects.filter(group=scope)
        if scope_type.type == self.type:
            return [scope]
        return []


class GroupUserObjectScopeType(ObjectScopeType):
    type = "group_user"
    model_class = GroupUser

    def get_parent_scope(self):
        return object_scope_type_registry.get("group")

    def get_parent(self, context):
        return context.group

    def get_all_context_objects_in_scope(self, scope):
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == GroupObjectScopeType.type:
            return GroupUser.objects.filter(group=scope)
        if scope_type.type == self.type:
            return [scope]
        return []

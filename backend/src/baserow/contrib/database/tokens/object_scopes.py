from typing import Iterable

from baserow.contrib.database.tokens.models import Token
from baserow.core.registries import ObjectScopeType, object_scope_type_registry
from baserow.core.types import ScopeObject


class TokenObjectScopeType(ObjectScopeType):

    type = "token"
    model_class = Token

    def get_parent_scope(self):
        return object_scope_type_registry.get("group")

    def get_parent(self, context):
        return context.group

    def get_all_context_objects_in_scope(self, scope: ScopeObject) -> Iterable:
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == "group":
            return Token.objects.filter(group=scope.id)
        if scope_type.type == self.type:
            return [scope]
        return []

from abc import ABC

from baserow.contrib.database.tokens.object_scopes import TokenObjectScopeType
from baserow.core.operations import GroupCoreOperationType
from baserow.core.registries import OperationType


class CreateTokenOperationType(GroupCoreOperationType):
    type = "group.create_token"


class TokenOperationType(OperationType, ABC):
    context_scope_name = TokenObjectScopeType.type


class ReadTokenOperationType(TokenOperationType):
    type = "group.token.read"


class UpdateTokenOperationType(TokenOperationType):
    type = "group.token.update"


class UseTokenOperationType(TokenOperationType):
    type = "group.token.use"

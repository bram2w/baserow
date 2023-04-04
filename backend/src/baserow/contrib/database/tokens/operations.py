from abc import ABC

from baserow.contrib.database.tokens.object_scopes import TokenObjectScopeType
from baserow.core.operations import WorkspaceCoreOperationType
from baserow.core.registries import OperationType


class CreateTokenOperationType(WorkspaceCoreOperationType):
    type = "workspace.create_token"


class TokenOperationType(OperationType, ABC):
    context_scope_name = TokenObjectScopeType.type


class ReadTokenOperationType(TokenOperationType):
    type = "workspace.token.read"


class UpdateTokenOperationType(TokenOperationType):
    type = "workspace.token.update"


class UseTokenOperationType(TokenOperationType):
    type = "workspace.token.use"

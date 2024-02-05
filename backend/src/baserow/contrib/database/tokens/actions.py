import dataclasses
from typing import Dict, List, Tuple, Union

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.core.action.registries import ActionType, ActionTypeDescription
from baserow.core.action.scopes import (
    WORKSPACE_ACTION_CONTEXT,
    WorkspaceActionScopeType,
)
from baserow.core.models import Workspace

from .handler import TokenHandler
from .models import Token


class CreateDbTokenActionType(ActionType):
    type = "create_db_token"
    description = ActionTypeDescription(
        _("Create DB token"),
        _(
            'A Database Token with name "%(token_name)s" (%(token_id)s) has been created'
        ),
        WORKSPACE_ACTION_CONTEXT,
    )
    analytics_params = [
        "token_id",
        "workspace_id",
    ]

    @dataclasses.dataclass
    class Params:
        token_id: int
        token_name: str
        workspace_id: int
        workspace_name: str

    @classmethod
    def do(cls, user: AbstractUser, workspace: Workspace, name: str):
        token = TokenHandler().create_token(user, workspace, name)
        cls.register_action(
            user,
            cls.Params(token.id, token.name, workspace.id, workspace.name),
            cls.scope(workspace.id),
            workspace,
        )
        return token

    @classmethod
    def scope(cls, workspace_id: int):
        return WorkspaceActionScopeType.value(workspace_id)


class UpdateDbTokenNameActionType(ActionType):
    type = "update_db_token_name"
    description = ActionTypeDescription(
        _("Update DB token name"),
        _(
            'The Database Token (%(token_name)s) name changed from "%(original_token_name)s" to "%(token_name)s"'
        ),
        WORKSPACE_ACTION_CONTEXT,
    )
    analytics_params = [
        "token_id",
        "workspace_id",
    ]

    @dataclasses.dataclass
    class Params:
        token_id: int
        token_name: str
        workspace_id: int
        workspace_name: str
        original_token_name: str

    @classmethod
    def do(cls, user: AbstractUser, token: Token, name: str):
        original_token_name = token.name
        workspace = token.workspace

        token = TokenHandler().update_token(user, token, name)

        cls.register_action(
            user,
            cls.Params(
                token.id, token.name, workspace.id, workspace.name, original_token_name
            ),
            cls.scope(workspace.id),
            workspace,
        )
        return token

    @classmethod
    def scope(cls, workspace_id: int):
        return WorkspaceActionScopeType.value(workspace_id)


class UpdateDbTokenPermissionsActionType(ActionType):
    type = "update_db_token_permissions"
    description = ActionTypeDescription(
        _("Update DB token permissions"),
        _(
            'The Database Token "%(token_name)s" (%(token_id)s) permissions has been updated'
        ),
        WORKSPACE_ACTION_CONTEXT,
    )
    analytics_params = [
        "token_id",
        "workspace_id",
        "token_permissions",
        "original_token_permissions",
    ]

    @dataclasses.dataclass
    class Params:
        token_id: int
        token_name: str
        token_permissions: List[Dict[str, Union[str, int]]]
        workspace_id: int
        workspace_name: str
        original_token_permissions: List[Dict[str, Union[str, int]]]

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        token: Token,
        **permissions: Dict[str, Union[bool, List[Tuple[str, int]]]],
    ):
        original_token_permissions = list(
            token.tokenpermission_set.values("type", "database", "table")
        )
        workspace = token.workspace

        TokenHandler().update_token_permissions(user, token, **permissions)
        token_permissions = list(
            token.tokenpermission_set.values("type", "database", "table")
        )

        cls.register_action(
            user,
            cls.Params(
                token.id,
                token.name,
                token_permissions,
                workspace.id,
                workspace.name,
                original_token_permissions,
            ),
            cls.scope(workspace.id),
            workspace,
        )

    @classmethod
    def scope(cls, workspace_id: int):
        return WorkspaceActionScopeType.value(workspace_id)


class RotateDbTokenKeyActionType(ActionType):
    type = "rotate_db_token_key"
    description = ActionTypeDescription(
        _("Rotate DB token key"),
        _('The Database Token "%(token_name)s" (%(token_id)s) has been rotated'),
        WORKSPACE_ACTION_CONTEXT,
    )
    analytics_params = [
        "token_id",
        "workspace_id",
    ]

    @dataclasses.dataclass
    class Params:
        token_id: int
        token_name: int
        workspace_id: int
        workspace_name: str

    @classmethod
    def do(cls, user: AbstractUser, token: Token):
        token = TokenHandler().rotate_token_key(user, token)

        workspace = token.workspace
        cls.register_action(
            user,
            cls.Params(token.id, token.name, workspace.id, workspace.name),
            cls.scope(workspace.id),
            workspace,
        )
        return token

    @classmethod
    def scope(cls, workspace_id: int):
        return WorkspaceActionScopeType.value(workspace_id)


class DeleteDbTokenActionType(ActionType):
    type = "delete_db_token_key"
    description = ActionTypeDescription(
        _("Delete DB token"),
        _('The Database Token "%(token_name)s" (%(token_id)s) has been deleted'),
        WORKSPACE_ACTION_CONTEXT,
    )
    analytics_params = [
        "token_id",
        "workspace_id",
    ]

    @dataclasses.dataclass
    class Params:
        token_id: int
        token_name: int
        workspace_id: int
        workspace_name: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        token: Token,
    ):
        workspace = token.workspace
        TokenHandler().delete_token(user, token)

        cls.register_action(
            user,
            cls.Params(token.id, token.name, workspace.id, workspace.name),
            cls.scope(workspace.id),
            workspace,
        )

    @classmethod
    def scope(cls, workspace_id: int):
        return WorkspaceActionScopeType.value(workspace_id)

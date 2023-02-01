import dataclasses
from typing import Dict, List, Tuple, Union

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.core.action.registries import ActionType, ActionTypeDescription
from baserow.core.action.scopes import GROUP_ACTION_CONTEXT, GroupActionScopeType
from baserow.core.models import Group

from .handler import TokenHandler
from .models import Token


class CreateDbTokenActionType(ActionType):
    type = "create_db_token"
    description = ActionTypeDescription(
        _("Create DB token"),
        _(
            'A Database Token with name "%(token_name)s" (%(token_id)s) has been created'
        ),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        token_id: int
        token_name: str
        group_id: int
        group_name: str

    @classmethod
    def do(cls, user: AbstractUser, group: Group, name: str):
        token = TokenHandler().create_token(user, group, name)
        cls.register_action(
            user,
            cls.Params(token.id, token.name, group.id, group.name),
            cls.scope(group.id),
            group,
        )
        return token

    @classmethod
    def scope(cls, group_id: int):
        return GroupActionScopeType.value(group_id)


class UpdateDbTokenNameActionType(ActionType):
    type = "update_db_token_name"
    description = ActionTypeDescription(
        _("Update DB token name"),
        _(
            'The Database Token (%(token_name)s) name changed from "%(original_token_name)s" to "%(token_name)s"'
        ),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        token_id: int
        token_name: str
        group_id: int
        group_name: str
        original_token_name: str

    @classmethod
    def do(cls, user: AbstractUser, token: Token, name: str):
        original_token_name = token.name
        group = token.group

        token = TokenHandler().update_token(user, token, name)

        cls.register_action(
            user,
            cls.Params(token.id, token.name, group.id, group.name, original_token_name),
            cls.scope(group.id),
            group,
        )
        return token

    @classmethod
    def scope(cls, group_id: int):
        return GroupActionScopeType.value(group_id)


class UpdateDbTokenPermissionsActionType(ActionType):
    type = "update_db_token_permissions"
    description = ActionTypeDescription(
        _("Update DB token permissions"),
        _(
            'The Database Token "%(token_name)s" (%(token_id)s) permissions has been updated'
        ),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        token_id: int
        token_name: str
        token_permissions: List[Dict[str, Union[str, int]]]
        group_id: int
        group_name: str
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
        group = token.group

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
                group.id,
                group.name,
                original_token_permissions,
            ),
            cls.scope(group.id),
            group,
        )

    @classmethod
    def scope(cls, group_id: int):
        return GroupActionScopeType.value(group_id)


class RotateDbTokenKeyActionType(ActionType):
    type = "rotate_db_token_key"
    description = ActionTypeDescription(
        _("Rotate DB token key"),
        _('The Database Token "%(token_name)s" (%(token_id)s) has been rotated'),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        token_id: int
        token_name: int
        group_id: int
        group_name: str

    @classmethod
    def do(cls, user: AbstractUser, token: Token):

        token = TokenHandler().rotate_token_key(user, token)

        group = token.group
        cls.register_action(
            user,
            cls.Params(token.id, token.name, group.id, group.name),
            cls.scope(group.id),
            group,
        )
        return token

    @classmethod
    def scope(cls, group_id: int):
        return GroupActionScopeType.value(group_id)


class DeleteDbTokenActionType(ActionType):
    type = "delete_db_token_key"
    description = ActionTypeDescription(
        _("Delete DB token"),
        _('The Database Token "%(token_name)s" (%(token_id)s) has been deleted'),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        token_id: int
        token_name: int
        group_id: int
        group_name: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        token: Token,
    ):

        group = token.group
        TokenHandler().delete_token(user, token)

        cls.register_action(
            user,
            cls.Params(token.id, token.name, group.id, group.name),
            cls.scope(group.id),
            group,
        )

    @classmethod
    def scope(cls, group_id: int):
        return GroupActionScopeType.value(group_id)

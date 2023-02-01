import dataclasses
from typing import Any, Dict, Optional

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.core.action.registries import ActionType, ActionTypeDescription
from baserow.core.action.scopes import GROUP_ACTION_CONTEXT, GroupActionScopeType
from baserow.core.exceptions import ApplicationDoesNotExist, GroupDoesNotExist
from baserow.core.models import Application, Group
from baserow.core.trash.handler import TrashHandler


class EmptyTrashActionType(ActionType):
    type = "empty_trash"
    description = ActionTypeDescription(
        _("Empty trash"),
        _(
            'Trash for application "%(application_name)s" (%(application_id)s) has been emptied'
        ),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        group_id: int
        group_name: str
        application_id: Optional[int] = None
        application_name: Optional[str] = None

    @classmethod
    def _get_application(cls, application_id: int):
        try:
            return Application.objects_and_trash.get(id=application_id)
        except Application.DoesNotExist:
            raise ApplicationDoesNotExist

    @classmethod
    def _get_group(cls, group_id: int):
        try:
            return Group.objects_and_trash.get(id=group_id)
        except Group.DoesNotExist:
            raise GroupDoesNotExist

    @classmethod
    def do(
        cls, user: AbstractUser, group_id: int, application_id: Optional[int] = None
    ):
        application_name = None
        group = None
        if application_id is not None:
            application = cls._get_application(application_id)
            application_name = application.name
            group = application.group
        else:
            group = cls._get_group(group_id)

        TrashHandler().empty(user, group_id, application_id)

        cls.register_action(
            user,
            cls.Params(group_id, group.name, application_id, application_name),
            cls.scope(group_id),
            group,
        )

    @classmethod
    def scope(cls, group_id: int):
        return GroupActionScopeType.value(group_id)

    @classmethod
    def get_long_description(cls, params_dict: Dict[str, Any], *args, **kwargs) -> str:
        if params_dict.get("application_id") is None:
            return (
                _('Trash for group "%(group_name)s" (%(group_id)s) has been emptied.')
                % params_dict
            )

        return super().get_long_description(params_dict, *args, **kwargs)


class RestoreFromTrashActionType(ActionType):
    type = "restore_from_trash"
    description = ActionTypeDescription(
        _("Restore from trash"),
        _('Item of type "%(item_type)s" (%(item_id)s) has been restored from trash'),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        item_id: int
        item_type: str
        group_id: int
        group_name: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        trash_item_type: str,
        trash_item_id: int,
        parent_trash_item_id: Optional[int] = None,
    ):
        trash_entry = TrashHandler.get_trash_entry(
            trash_item_type, trash_item_id, parent_trash_item_id
        )
        group = trash_entry.group
        TrashHandler.restore_item(
            user, trash_item_type, trash_item_id, parent_trash_item_id
        )

        cls.register_action(
            user,
            cls.Params(trash_item_id, trash_item_type, group.id, group.name),
            cls.scope(group.id),
            group,
        )

    @classmethod
    def scope(cls, group_id: int):
        return GroupActionScopeType.value(group_id)

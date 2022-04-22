import dataclasses
from typing import Any, List

from django.contrib.auth.models import AbstractUser

from baserow.core.action.models import Action
from baserow.core.action.registries import ActionType, ActionScopeStr
from baserow.core.action.scopes import RootActionScopeType, GroupActionScopeType
from baserow.core.handler import GroupForUpdate, CoreHandler
from baserow.core.models import GroupUser, Group, Application
from baserow.core.trash.handler import TrashHandler


class DeleteGroupActionType(ActionType):
    type = "delete_group"

    @dataclasses.dataclass
    class Params:
        deleted_group_id: int

    def do(self, user: AbstractUser, group: GroupForUpdate):
        """
        Deletes an existing group and related applications if the user has admin
        permissions for the group. See baserow.core.handler.CoreHandler.delete_group
        for more details. Undoing this action restores the group, redoing it deletes it
        again.

        :param user: The user performing the delete.
        :param group: A LockedGroup obtained from CoreHandler.get_group_for_update which
            will be deleted.
        """

        CoreHandler().delete_group(user, group)

        self.register_action(user, self.Params(group.id), scope=self.scope())

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()

    @classmethod
    def undo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_undo: Action,
    ):
        TrashHandler.restore_item(
            user,
            "group",
            params.deleted_group_id,
        )

    @classmethod
    def redo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_redo: Action,
    ):
        CoreHandler().delete_group_by_id(user, params.deleted_group_id)


class CreateGroupActionType(ActionType):
    type = "create_group"

    @dataclasses.dataclass
    class Params:
        group_id: int
        group_name: str

    @classmethod
    def do(cls, user: AbstractUser, group_name: str) -> GroupUser:
        """
        Creates a new group for an existing user. See
        baserow.core.handler.CoreHandler.create_group for more details. Undoing this
        action deletes the created group, redoing it restores it from the trash.

        :param user: The user creating the group.
        :param group_name: The name to give the group.
        """

        group_user = CoreHandler().create_group(user, name=group_name)

        # noinspection PyTypeChecker
        group_id: int = group_user.group_id

        cls.register_action(
            user=user,
            params=cls.Params(group_id, group_name),
            scope=cls.scope(),
        )
        return group_user

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()

    @classmethod
    def undo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_undo: Action,
    ):
        CoreHandler().delete_group_by_id(user, params.group_id)

    @classmethod
    def redo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_redo: Action,
    ):
        TrashHandler.restore_item(
            user, "group", params.group_id, parent_trash_item_id=None
        )


class UpdateGroupActionType(ActionType):
    type = "update_group"

    @dataclasses.dataclass
    class Params:
        group_id: int
        original_group_name: str
        new_group_name: str

    @classmethod
    def do(
        cls, user: AbstractUser, group: GroupForUpdate, new_group_name: str
    ) -> GroupForUpdate:
        """
        Updates the values of a group if the user has admin permissions to the group.
        See baserow.core.handler.CoreHandler.upgrade_group for more details. Undoing
        this action restores the name of the group prior to this action being performed,
        redoing this restores the new name set initially.

        :param user: The user creating the group.
        :param group: A LockedGroup obtained from CoreHandler.get_group_for_update on
            which the update will be run.
        :param new_group_name: The new name to give the group.
        :returns: The updated group.
        """

        original_group_name = group.name
        CoreHandler().update_group(user, group, name=new_group_name)

        cls.register_action(
            user=user,
            params=cls.Params(
                group.id,
                original_group_name=original_group_name,
                new_group_name=new_group_name,
            ),
            scope=cls.scope(),
        )
        return group

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()

    @classmethod
    def undo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_undo: Action,
    ):
        group = CoreHandler().get_group_for_update(params.group_id)
        CoreHandler().update_group(
            user,
            group,
            name=params.original_group_name,
        )

    @classmethod
    def redo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_redo: Action,
    ):
        group = CoreHandler().get_group_for_update(params.group_id)
        CoreHandler().update_group(
            user,
            group,
            name=params.new_group_name,
        )


class OrderGroupsActionType(ActionType):
    type = "order_groups"

    @dataclasses.dataclass
    class Params:
        original_order: List[int]
        new_order: List[int]

    @classmethod
    def do(cls, user: AbstractUser, group_ids: List[int]) -> None:
        """
        Changes the order of groups for a user.
        See baserow.core.handler.CoreHandler.order_groups for more details. Undoing
        this action restores the original order of groups prior to this action being
        performed, redoing this restores the new order set initially.

        :param user: The user ordering the groups.
        :param group_ids: The ids of the groups to order.
        """

        original_order = CoreHandler().get_groups_order(user)

        CoreHandler().order_groups(user, group_ids)

        cls.register_action(
            user=user,
            params=cls.Params(
                original_order,
                new_order=group_ids,
            ),
            scope=cls.scope(),
        )

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()

    @classmethod
    def undo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_undo: Action,
    ):
        CoreHandler().order_groups(user, params.original_order)

    @classmethod
    def redo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_redo: Action,
    ):
        CoreHandler().order_groups(user, params.new_order)


class CreateApplicationActionType(ActionType):
    type = "create_application"

    @dataclasses.dataclass
    class Params:
        application_id: int

    @classmethod
    def do(
        cls, user: AbstractUser, group: Group, application_type: str, name: str
    ) -> Any:
        """
        Creates a new application based on the provided type. See
        baserow.core.handler.CoreHandler.create_application for further details.
        Undoing this action trashes the application and redoing restores it.

        :param user: The user creating the application.
        :param group: The group to create the application in.
        :param application_type: The type of application to create.
        :param name: The name of the new application.
        :return: The created Application model instance.
        """

        application = CoreHandler().create_application(
            user, group, application_type, name=name
        )

        params = cls.Params(application.id)
        cls.register_action(user, params, cls.scope(group.id))

        return application

    @classmethod
    def scope(cls, group_id) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        application = Application.objects.get(id=params.application_id)
        CoreHandler().delete_application(user, application)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TrashHandler.restore_item(
            user, "application", params.application_id, parent_trash_item_id=None
        )

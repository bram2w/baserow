import dataclasses
from typing import Any, List, Optional

from django.contrib.auth.models import AbstractUser

from baserow.core.action.models import Action
from baserow.core.action.registries import ActionScopeStr, ActionType
from baserow.core.action.scopes import GroupActionScopeType, RootActionScopeType
from baserow.core.handler import CoreHandler, GroupForUpdate
from baserow.core.models import Application, Group, GroupUser, Template
from baserow.core.trash.handler import TrashHandler
from baserow.core.utils import ChildProgressBuilder


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
        :return: The updated group.
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


class OrderApplicationsActionType(ActionType):
    type = "order_applications"

    @dataclasses.dataclass
    class Params:
        group_id: int
        original_application_ids: List[int]
        new_application_ids: List[int]

    @classmethod
    def do(
        cls, user: AbstractUser, group: Group, application_ids_in_order: List[int]
    ) -> Any:
        """
        Reorders the applications of a given group in the desired order. The index of
        the id in the list will be the new order. See
        `baserow.core.handler.CoreHandler.order_applications` for further details. When
        undone re-orders the applications back to the old order, when redone reorders
        to the new order.

        :param user: The user on whose behalf the applications are reordered.
        :param group: The group where the applications are in.
        :param application_ids_in_order: A list of ids in the new order.
        """

        old_ids_in_order = list(
            CoreHandler().order_applications(user, group, application_ids_in_order)
        )

        params = cls.Params(
            group_id=group.id,
            original_application_ids=old_ids_in_order,
            new_application_ids=application_ids_in_order,
        )
        cls.register_action(user, params, cls.scope(group.id))

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        group = CoreHandler().get_group_for_update(params.group_id)
        CoreHandler().order_applications(user, group, params.original_application_ids)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        group = CoreHandler().get_group_for_update(params.group_id)
        CoreHandler().order_applications(user, group, params.new_application_ids)


class CreateApplicationActionType(ActionType):
    type = "create_application"

    @dataclasses.dataclass
    class Params:
        application_id: int

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        group: Group,
        application_type: str,
        name: str,
        init_with_data: bool = False,
    ) -> Any:
        """
        Creates a new application based on the provided type. See
        baserow.core.handler.CoreHandler.create_application for further details.
        Undoing this action trashes the application and redoing restores it.

        :param user: The user creating the application.
        :param group: The group to create the application in.
        :param application_type: The type of application to create.
        :param name: The name of the new application.
        :param init_with_data: Whether the application should be initialized with
            some default data. Defaults to False.
        :return: The created Application model instance.
        """

        application = CoreHandler().create_application(
            user, group, application_type, name=name, init_with_data=init_with_data
        )

        params = cls.Params(application.id)
        cls.register_action(user, params, cls.scope(group.id))

        return application

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
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


class DeleteApplicationActionType(ActionType):
    type = "delete_application"

    @dataclasses.dataclass
    class Params:
        application_id: int

    @classmethod
    def do(cls, user: AbstractUser, application: Application) -> None:
        """
        Deletes an existing application instance if the user has access to the
        related group. The `application_deleted` signal is also called.
        See baserow.core.handler.CoreHandler.delete_application for further details.
        Undoing this action restores the application and redoing trashes it.

        :param user: The user on whose behalf the application is deleted.
        :param application: The application instance that needs to be deleted.
        """

        CoreHandler().delete_application(user, application)

        params = cls.Params(application.id)
        cls.register_action(user, params, cls.scope(application.group.id))

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user, params: Params, action_being_undone: Action):
        TrashHandler.restore_item(
            user, "application", params.application_id, parent_trash_item_id=None
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        application = CoreHandler().get_application(params.application_id)
        CoreHandler().delete_application(user, application)


class UpdateApplicationActionType(ActionType):
    type = "update_application"

    @dataclasses.dataclass
    class Params:
        application_id: int
        original_name: str
        new_name: str

    @classmethod
    def do(cls, user: AbstractUser, application: Application, name: str) -> Application:
        """
        Updates an existing application instance.
        See baserow.core.handler.CoreHandler.update_application for further details.
        Undoing this action restore the original_name while redoing set name again.

        :param user: The user on whose behalf the application is updated.
        :param application: The application instance that needs to be updated.
        :param name: The new name of the application.
        :raises ValueError: If one of the provided parameters is invalid.
        :return: The updated application instance.
        """

        original_name = application.name

        application = CoreHandler().update_application(user, application, name)

        params = cls.Params(application.id, original_name, name)
        cls.register_action(user, params, cls.scope(application.group.id))

        return application

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        application = CoreHandler().get_application(params.application_id)
        CoreHandler().update_application(user, application, params.original_name)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        application = CoreHandler().get_application(params.application_id)
        CoreHandler().update_application(user, application, params.new_name)


class DuplicateApplicationActionType(ActionType):
    type = "duplicate_application"

    @dataclasses.dataclass
    class Params:
        application_id: int

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        application: Application,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> Application:
        """
        Duplicate an existing application instance.
        See baserow.core.handler.CoreHandler.duplicate_application for further details.
        Undoing this action trashes the application and redoing restores it.

        :param user: The user on whose behalf the application is duplicated.
        :param application: The application instance that needs to be duplicated.
        :param progress_builder: A progress builder instance that can be used to
            track the progress of the duplication.
        :return: The new (duplicated) application instance.
        """

        new_application_clone = CoreHandler().duplicate_application(
            user,
            application,
            progress_builder,
        )

        params = cls.Params(new_application_clone.id)
        cls.register_action(user, params, cls.scope(application.group.id))

        return new_application_clone

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        application = CoreHandler().get_application(params.application_id)
        CoreHandler().delete_application(user, application)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TrashHandler.restore_item(
            user, "application", params.application_id, parent_trash_item_id=None
        )


class InstallTemplateActionType(ActionType):
    type = "install_template"

    @dataclasses.dataclass
    class Params:
        installed_applications_ids: List[int]

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        group: Group,
        template: Template,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> List[Application]:
        """
        Install a template into the provided group. See
        baserow.core.handler.CoreHandler.install_template for further details.
        Undoing this action trash the installed applications and redoing
        restore them all.

        :param user: The user on whose behalf the template is installed.
        :param group: The group where the applications will be installed.
        :param template: The template to install.
        :param progress_builder: A progress builder instance that can be used to
            track the progress of the installation.
        :return: The list of installed applications.
        """

        installed_applications, _ = CoreHandler().install_template(
            user,
            group,
            template,
            progress_builder=progress_builder,
        )

        params = cls.Params([app.id for app in installed_applications])
        cls.register_action(user, params, cls.scope(group.id))

        return installed_applications

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        handler = CoreHandler()
        for application_id in params.installed_applications_ids:
            application = CoreHandler().get_application(application_id)
            handler.delete_application(user, application)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        for application_id in params.installed_applications_ids:
            TrashHandler.restore_item(
                user, "application", application_id, parent_trash_item_id=None
            )

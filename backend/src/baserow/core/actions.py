import dataclasses
from typing import Any, List, Optional

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.core.action.models import Action
from baserow.core.action.registries import (
    ActionScopeStr,
    ActionType,
    ActionTypeDescription,
    UndoableActionType,
)
from baserow.core.action.scopes import (
    GROUP_ACTION_CONTEXT,
    GroupActionScopeType,
    RootActionScopeType,
)
from baserow.core.handler import CoreHandler, GroupForUpdate
from baserow.core.models import Application, Group, GroupInvitation, GroupUser, Template
from baserow.core.registries import application_type_registry
from baserow.core.trash.handler import TrashHandler
from baserow.core.utils import ChildProgressBuilder


class DeleteGroupActionType(UndoableActionType):
    type = "delete_group"

    description = ActionTypeDescription(
        _("Delete group"),
        _('Group "%(group_name)s" (%(group_id)s) deleted.'),
    )

    @dataclasses.dataclass
    class Params:
        group_id: int
        group_name: str

    @classmethod
    def do(cls, user: AbstractUser, group: GroupForUpdate):
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

        cls.register_action(
            user=user,
            params=cls.Params(group.id, group.name),
            scope=cls.scope(),
            group=group,
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
        TrashHandler.restore_item(
            user,
            "group",
            params.group_id,
        )

    @classmethod
    def redo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_redo: Action,
    ):
        CoreHandler().delete_group_by_id(user, params.group_id)


class CreateGroupActionType(UndoableActionType):
    type = "create_group"
    description = ActionTypeDescription(
        _("Create group"),
        _('Group "%(group_name)s" (%(group_id)s) created.'),
    )

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
        group = group_user.group

        cls.register_action(
            user=user,
            params=cls.Params(group.id, group_name),
            scope=cls.scope(),
            group=group,
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


class UpdateGroupActionType(UndoableActionType):
    type = "update_group"
    description = ActionTypeDescription(
        _("Update group"),
        _(
            "Group (%(group_id)s) name changed from "
            '"%(original_group_name)s" to "%(group_name)s."'
        ),
    )

    @dataclasses.dataclass
    class Params:
        group_id: int
        group_name: str
        original_group_name: str

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
                group_name=new_group_name,
                original_group_name=original_group_name,
            ),
            scope=cls.scope(),
            group=group,
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
            name=params.group_name,
        )


class OrderGroupsActionType(UndoableActionType):
    type = "order_groups"
    description = ActionTypeDescription(
        _("Order groups"),
        _("Groups order changed."),
    )

    @dataclasses.dataclass
    class Params:
        group_ids: List[int]
        original_group_ids: List[int]

    @classmethod
    def do(cls, user: AbstractUser, group_ids_in_order: List[int]) -> None:
        """
        Changes the order of groups for a user.
        See baserow.core.handler.CoreHandler.order_groups for more details. Undoing
        this action restores the original order of groups prior to this action being
        performed, redoing this restores the new order set initially.

        :param user: The user ordering the groups.
        :param group_ids: The ids of the groups to order.
        """

        original_group_ids_in_order = CoreHandler().get_groups_order(user)

        CoreHandler().order_groups(user, group_ids_in_order)

        cls.register_action(
            user=user,
            params=cls.Params(
                group_ids_in_order,
                original_group_ids_in_order,
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
        CoreHandler().order_groups(user, params.original_group_ids)

    @classmethod
    def redo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_redo: Action,
    ):
        CoreHandler().order_groups(user, params.group_ids)


class OrderApplicationsActionType(UndoableActionType):
    type = "order_applications"
    description = ActionTypeDescription(
        _("Order applications"), _("Applications reordered"), GROUP_ACTION_CONTEXT
    )

    @dataclasses.dataclass
    class Params:
        group_id: int
        group_name: str
        application_ids: List[int]
        original_application_ids: List[int]

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

        original_application_ids_in_order = list(
            CoreHandler().order_applications(user, group, application_ids_in_order)
        )

        params = cls.Params(
            group.id,
            group.name,
            application_ids_in_order,
            original_application_ids_in_order,
        )
        cls.register_action(user, params, scope=cls.scope(group.id), group=group)

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
        CoreHandler().order_applications(user, group, params.application_ids)


class CreateApplicationActionType(UndoableActionType):
    type = "create_application"
    description = ActionTypeDescription(
        _("Create application"),
        _('"%(application_name)s" (%(application_id)s) %(application_type)s created'),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        group_id: int
        group_name: str
        application_type: str
        application_id: int
        application_name: str
        with_data: bool

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

        application_type = application_type_registry.get_by_model(
            application.specific_class
        )

        params = cls.Params(
            group.id,
            group.name,
            application_type.type,
            application.id,
            application.name,
            init_with_data,
        )
        cls.register_action(user, params, scope=cls.scope(group.id), group=group)

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


class DeleteApplicationActionType(UndoableActionType):
    type = "delete_application"
    description = ActionTypeDescription(
        _("Delete application"),
        _(
            'Application "%(application_name)s" (%(application_id)s) of type '
            "%(application_type)s deleted"
        ),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        group_id: int
        group_name: str
        application_type: str
        application_id: int
        application_name: str

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

        group = application.group
        application_type = application_type_registry.get_by_model(
            application.specific_class
        )
        params = cls.Params(
            group.id,
            group.name,
            application_type.type,
            application.id,
            application.name,
        )
        cls.register_action(
            user, params, scope=cls.scope(application.group.id), group=group
        )

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


class UpdateApplicationActionType(UndoableActionType):
    type = "update_application"
    description = ActionTypeDescription(
        _("Update application"),
        _(
            "Application (%(application_id)s) of type %(application_type)s renamed "
            'from "%(original_application_name)s" to "%(application_name)s"'
        ),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        group_id: int
        group_name: str
        application_type: str
        application_id: int
        application_name: str
        original_application_name: str

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
        application_type = application_type_registry.get_by_model(
            application.specific_class
        )
        group = application.group

        params = cls.Params(
            group.id,
            group.name,
            application_type.type,
            application.id,
            name,
            original_name,
        )
        cls.register_action(
            user, params, scope=cls.scope(application.group.id), group=group
        )

        return application

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        application = CoreHandler().get_application(params.application_id)
        CoreHandler().update_application(
            user, application, params.original_application_name
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        application = CoreHandler().get_application(params.application_id)
        CoreHandler().update_application(user, application, params.application_name)


class DuplicateApplicationActionType(UndoableActionType):
    type = "duplicate_application"
    description = ActionTypeDescription(
        _("Duplicate application"),
        _(
            'Application "%(application_name)s" (%(application_id)s) of type %(application_type)s '
            'duplicated from "%(original_application_name)s" (%(original_application_id)s)'
        ),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        group_id: int
        group_name: str
        application_type: str
        application_id: int
        application_name: str
        original_application_id: int
        original_application_name: str

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

        new_app_clone = CoreHandler().duplicate_application(
            user,
            application,
            progress_builder,
        )
        application_type = application_type_registry.get_by_model(
            application.specific_class
        )
        group = application.group

        params = cls.Params(
            group.id,
            group.name,
            application_type.type,
            new_app_clone.id,
            new_app_clone.name,
            application.id,
            application.name,
        )
        cls.register_action(user, params, cls.scope(application.group.id), group=group)

        return new_app_clone

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


class InstallTemplateActionType(UndoableActionType):
    type = "install_template"
    description = ActionTypeDescription(
        _("Install template"),
        _(
            'Template "%(template_name)s" (%(template_id)s) installed '
            "into application IDs %(installed_application_ids)s"
        ),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        group_id: int
        group_name: str
        template_id: int
        template_name: str
        installed_application_ids: List[int]

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

        params = cls.Params(
            group.id,
            group.name,
            template.id,
            template.name,
            [app.id for app in installed_applications],
        )
        cls.register_action(user, params, scope=cls.scope(group.id), group=group)

        return installed_applications

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        handler = CoreHandler()
        for application_id in params.installed_application_ids:
            application = CoreHandler().get_application(application_id)
            handler.delete_application(user, application)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        for application_id in params.installed_application_ids:
            TrashHandler.restore_item(
                user, "application", application_id, parent_trash_item_id=None
            )


class CreateGroupInvitationActionType(ActionType):
    type = "create_group_invitation"
    description = ActionTypeDescription(
        _("Create group invitation"),
        _(
            'Group invitation created for "%(email)s" to join '
            '"%(group_name)s" (%(group_id)s) as %(permissions)s.'
        ),
    )

    @dataclasses.dataclass
    class Params:
        email: str
        permissions: str
        group_id: int
        group_name: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        group: Group,
        email: str,
        permissions: str,
        base_url: str,
        message: str = "",
    ) -> GroupInvitation:
        """
        Creates a new group invitation for the given email address and sends out an
        email containing the invitation.
        Look into baserow.core.handler.CoreHandler.create_group_invitation for further
        details.


        """

        group_invitation = CoreHandler().create_group_invitation(
            user, group, email, permissions, base_url, message
        )

        cls.register_action(
            user=user,
            params=cls.Params(email, permissions, group.id, group.name),
            scope=cls.scope(),
            group=group,
        )
        return group_invitation

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()


class DeleteGroupInvitationActionType(ActionType):
    type = "delete_group_invitation"
    description = ActionTypeDescription(
        _("Delete group invitation"),
        _(
            'Group invitation (%(invitation_id)s) deleted for "%(email)s" '
            'to join "%(group_name)s" (%(group_id)s) as %(permissions)s.'
        ),
    )

    @dataclasses.dataclass
    class Params:
        invitation_id: int
        email: str
        permissions: str
        group_id: int
        group_name: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        group_invitation: GroupInvitation,
    ):
        """
        Deletes an existing group invitation.
        Look into baserow.core.handler.CoreHandler.delete_group_invitation for further
        details.


        """

        group = group_invitation.group
        params = cls.Params(
            group_invitation.id,
            group_invitation.email,
            group_invitation.permissions,
            group.id,
            group.name,
        )
        CoreHandler().delete_group_invitation(user, group_invitation)

        cls.register_action(
            user=user,
            params=params,
            scope=cls.scope(),
            group=group,
        )
        return group_invitation

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()


class AcceptGroupInvitationActionType(ActionType):
    type = "accept_group_invitation"
    description = ActionTypeDescription(
        _("Accept group invitation"),
        _(
            'Invitation (%(invitation_id)s) sent by "%(sender)s" to join '
            '"%(group_name)s" (%(group_id)s) as %(permissions)s was accepted.'
        ),
    )

    @dataclasses.dataclass
    class Params:
        invitation_id: int
        sender: str
        permissions: str
        group_id: int
        group_name: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        group_invitation: GroupInvitation,
    ) -> GroupUser:
        """
        Accepts an existing group invitation.
        Look into baserow.core.handler.CoreHandler.accept_group_invitation for further
        details.
        """

        group = group_invitation.group
        params = cls.Params(
            group_invitation.id,
            group_invitation.invited_by.email,
            group_invitation.permissions,
            group.id,
            group.name,
        )
        group_user = CoreHandler().accept_group_invitation(user, group_invitation)

        cls.register_action(
            user=user,
            params=params,
            scope=cls.scope(),
            group=group,
        )
        return group_user

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()


class RejectGroupInvitationActionType(ActionType):
    type = "reject_group_invitation"
    description = ActionTypeDescription(
        _("Reject group invitation"),
        _(
            'Invitation (%(invitation_id)s) sent by "%(sender)s" to join '
            '"%(group_name)s" (%(group_id)s) as %(permissions)s was rejected.'
        ),
    )

    @dataclasses.dataclass
    class Params:
        invitation_id: int
        sender: str
        permissions: str
        group_id: int
        group_name: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        group_invitation: GroupInvitation,
    ) -> GroupUser:
        """
        Accepts an existing group invitation.
        Look into baserow.core.handler.CoreHandler.reject_group_invitation for further
        details.
        """

        group = group_invitation.group
        params = cls.Params(
            group_invitation.id,
            group_invitation.invited_by.email,
            group_invitation.permissions,
            group.id,
            group.name,
        )
        group_user = CoreHandler().reject_group_invitation(user, group_invitation)

        cls.register_action(
            user=user,
            params=params,
            scope=cls.scope(),
            group=group,
        )
        return group_user

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()


class UpdateGroupInvitationActionType(ActionType):
    type = "update_group_invitation_permissions"
    description = ActionTypeDescription(
        _("Update group invitation permissions"),
        _(
            "Invitation (%(invitation_id)s) permissions changed from "
            "%(original_permissions)s to %(permissions)s for %(email)s "
            ' on group "%(group_name)s" (%(group_id)s).'
        ),
    )

    @dataclasses.dataclass
    class Params:
        invitation_id: int
        email: str
        permissions: str
        group_id: int
        group_name: str
        original_permissions: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        group_invitation: GroupInvitation,
        permissions: str,
    ) -> GroupInvitation:
        """
        Updates an existing group invitation permissions.
        Look into baserow.core.handler.CoreHandler.update_group_invitation for further
        details.
        """

        group = group_invitation.group
        params = cls.Params(
            group_invitation.id,
            group_invitation.email,
            permissions,
            group.id,
            group.name,
            original_permissions=group_invitation.permissions,
        )
        group_invitation = CoreHandler().update_group_invitation(
            user, group_invitation, permissions
        )

        cls.register_action(
            user=user,
            params=params,
            scope=cls.scope(),
            group=group,
        )
        return group_invitation

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()


class LeaveGroupActionType(ActionType):
    type = "leave_group"
    description = ActionTypeDescription(
        _("Leave group"),
        _('Group "%(group_name)s" (%(group_id)s) left.'),
    )

    @dataclasses.dataclass
    class Params:
        group_id: int
        group_name: str

    @classmethod
    def do(cls, user: AbstractUser, group: Group):
        """
        Leaves an existing group.
        Look into baserow.core.handler.CoreHandler.leave_group for further details.
        """

        CoreHandler().leave_group(user, group)

        cls.register_action(
            user=user,
            params=cls.Params(group.id, group.name),
            scope=cls.scope(),
            group=group,
        )

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()

import dataclasses
from typing import Any, Optional

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.core.action.registries import (
    ActionScopeStr,
    ActionType,
    ActionTypeDescription,
)
from baserow.core.action.scopes import RootActionScopeType
from baserow.core.models import Template
from baserow.core.user.handler import UserHandler


class CreateUserActionType(ActionType):
    type = "create_user"
    description = ActionTypeDescription(
        _("Create User"),
        _(
            'User "%(user_email)s" (%(user_id)s) created '
            "(via invitation: %(with_invitation_token)s, "
            "from template: %(template_id)s)"
        ),
    )

    @dataclasses.dataclass
    class Params:
        user_id: int
        user_email: str
        group_id: Optional[int] = None
        group_name: Optional[str] = ""
        with_invitation_token: bool = False
        template_id: Optional[int] = None

    @classmethod
    def do(
        cls,
        name: str,
        email: str,
        password: str,
        language: str,
        group_invitation_token: Optional[str] = None,
        template: Optional[Template] = None,
    ) -> AbstractUser:
        """
        Creates a new user.

        :param name: The name of the user.
        :param email: The email address of the user.
        :param password: The password of the user.
        :param language: The language of the user.
        :param group_invitation_token: The group invitation token that will be used to
            add the user to a group.
        :param template: The template that will be used to create the user.
        :return: The created user.
        """

        user = UserHandler().create_user(
            name, email, password, language, group_invitation_token, template
        )

        group_id, group_name = None, None
        if user.default_group:
            group_id = user.default_group.id
            group_name = user.default_group.name

        cls.register_action(
            user=user,
            params=cls.Params(
                user.id,
                user.email,
                group_id,
                group_name,
                group_invitation_token is not None,
                template.id if template else None,
            ),
            scope=cls.scope(),
            group=user.default_group,
        )
        return user

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()


class UpdateUserActionType(ActionType):
    type = "update_user"
    description = ActionTypeDescription(
        _("Update User"),
        _('User "%(user_email)s" (%(user_id)s) updated'),
    )

    @dataclasses.dataclass
    class Params:
        user_id: int
        user_email: str
        first_name: Optional[str]
        language: Optional[str]

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        first_name: Optional[str] = None,
        language: Optional[str] = None,
        **kwargs: Any
    ) -> AbstractUser:
        """
        Updates user's data.

        :param user: The user that will be updated.
        :param data: The data that will be used to update the user.
        :return: The updated user.
        """

        user = UserHandler().update_user(user, first_name=first_name, language=language)

        cls.register_action(
            user=user,
            params=cls.Params(user.id, user.email, first_name, language),
            scope=cls.scope(),
        )
        return user

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()


class ScheduleUserDeletionActionType(ActionType):
    type = "schedule_user_deletion"
    description = ActionTypeDescription(
        _("Schedule user deletion"),
        _(
            'User "%(user_email)s" (%(user_id)s) scheduled to be deleted after grace time'
        ),
    )

    @dataclasses.dataclass
    class Params:
        user_id: int
        user_email: str

    @classmethod
    def do(cls, user: AbstractUser) -> AbstractUser:
        """
        Schedules the user for deletion.

        :param user: The user that will be updated.
        """

        UserHandler().schedule_user_deletion(user)

        cls.register_action(
            user=user, params=cls.Params(user.id, user.email), scope=cls.scope()
        )

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()


class CancelUserDeletionActionType(ActionType):
    type = "cancel_user_deletion"
    description = ActionTypeDescription(
        _("Cancel user deletion"),
        _(
            'User "%(user_email)s" (%(user_id)s) logged in cancelling the deletion process'
        ),
    )

    @dataclasses.dataclass
    class Params:
        user_id: int
        user_email: str

    @classmethod
    def do(cls, user: AbstractUser) -> AbstractUser:
        """
        Stops the deletion process for the user.

        :param user: The user that will be updated.
        """

        user = UserHandler().cancel_user_deletion(user)

        cls.register_action(
            user=user, params=cls.Params(user.id, user.email), scope=cls.scope()
        )
        return user

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()

import abc
import dataclasses
from typing import Any, NewType, Optional

from django.contrib.auth.models import AbstractUser
from rest_framework import serializers

from baserow.api.sessions import (
    get_client_undo_redo_action_group_id,
    get_untrusted_client_session_id,
)
from baserow.core.action.models import Action
from baserow.core.registry import Registry, Instance

# An alias type of a str (its exactly a str, just with a different name in the type
# system). We use this instead of a normal str for type safety ensuring
# only str's returned by ActionScopeType.value and
# ActionScopeType.valid_serializer_value_to_scope_str can be used in functions
# which are expecting an ActionScopeStr.
ActionScopeStr = NewType("Scope", str)


class ActionScopeType(abc.ABC, Instance):
    """
    When a ActionType occurs we save a Action model in the database with a particular
    scope. An ActionScopeType is a possible type of scope an action can be
    categorized into, ultimately represented by a string and stored in the db.

    For example, there is a GroupActionScopeType. When stored in the database
    actions in this scope have a scope value of "group10", "group999", etc.
    """

    @property
    @abc.abstractmethod
    def type(self) -> str:
        """
        Implement this to be an unique name to identify this type of action scope.
        """

        pass

    @classmethod
    @abc.abstractmethod
    def value(cls, *args, **kwargs) -> ActionScopeStr:
        """
        Implement and use this method for constructing an ActionScopeStr of this type
        programmatically. This should almost always be prefixed by cls.type to prevent
        scopes of one type clashing with another.

        The args and kwargs should be completely overridden by the implemented type to
        accept whatever parameters are needed to construct a specific str for this
        scope.

        For example an Action.do method will call this method
        to generate the scope for an Action model instance it is saving.
        """

        pass

    @abc.abstractmethod
    def get_request_serializer_field(self) -> serializers.Field:
        """
        Implement this to return the DRF Field serializer which will be used to
        deserialize API requests including action scopes. The deserialized value
        from API requests will then be provided to
        valid_serializer_value_to_scope_str.
        """

        pass

    @abc.abstractmethod
    def valid_serializer_value_to_scope_str(
        self, value: Any
    ) -> Optional[ActionScopeStr]:
        """
        Implement this to return an ActionScopeStr (an alias type for str) when
        given the valid value deserialized by get_request_serializer_field. The
        returned str will be used querying for actions by scope. If None is returned
        then this scope will not be used.
        """

        pass


class ActionScopeRegistry(Registry[ActionScopeType]):
    name = "action_scope"


class ActionType(Instance, abc.ABC):
    type: str = NotImplemented

    @dataclasses.dataclass
    class Params:
        """
        Override this dataclass with one specific for this ActionType. Store in this
        dataclass any data required when undoing or redoing. This dataclass will be
        converted to JSON and stored when calling cls.register_action. Then upon
        undo/redo it will be deserialized and passed into the undo/redo functions
        below for you to use.
        """

        pass

    @classmethod
    @abc.abstractmethod
    def do(cls, *args, **kwargs) -> Any:
        """
        Should return perform the desired action and call cls.register_action with
        params containing what is required to undo/redo in the methods below. Please
        change the signature to be what parameters you specifically need for this
        type.
        """

        pass

    @classmethod
    @abc.abstractmethod
    def scope(cls, *args, **kwargs) -> ActionScopeStr:
        """
        Should return the default action scope which actions of this type are stored
        in. Please change the signature to be what parameters you specifically need
        for this type.
        """

        pass

    @classmethod
    @abc.abstractmethod
    def undo(cls, user: AbstractUser, params: Any, action_being_undone: Action):
        """
        Should undo the action done by the `do` method above, this should never call
        another ActionType's.do method as that would register a new action which we
        do not want to do as the result of an undo.

        :param user: The user performing the undo.
        :param params: The deserialized cls.Params dataclass from the `do` method.
        :param action_being_undone: The action that is being undone.
        """

        pass

    @classmethod
    @abc.abstractmethod
    def redo(cls, user: AbstractUser, params: Any, action_being_redone: Action):
        """
        Should redo the action undone by the `undo` method above, this should never call
        another ActionType's.do method as that would register a new action which we
        do not want to do as the result of an redo.

        :param user: The user performing the redo.
        :param params: The deserialized cls.Params dataclass from the `do` method.
        :param action_being_redone: The action that is being redone.
        """

        pass

    @classmethod
    def register_action(
        cls,
        user: AbstractUser,
        params: Any,
        scope: ActionScopeStr,
    ) -> Action:
        """
        Registers a new action in the database using the untrusted client session id
        if set in the request headers.

        :param user: The user who performed the action.
        :param params: A dataclass to serialize and store with the action which will be
            provided when undoing and redoing it.
        :param scope: The scope in which this action occurred.
        """

        session = get_untrusted_client_session_id(user)
        action_group = get_client_undo_redo_action_group_id(user)

        action = Action.objects.create(
            user=user,
            type=cls.type,
            params=params,
            scope=scope,
            session=session,
            action_group=action_group,
        )
        return action

    @classmethod
    def clean_up_any_extra_action_data(cls, action_being_cleaned_up: Action):
        """
        Should cleanup any extra data associated with the action as it has expired.

        :param action_being_cleaned_up: The action that is old and being cleaned up.
        """

        pass

    @classmethod
    def has_custom_cleanup(cls) -> bool:
        # noinspection PyUnresolvedReferences
        return (
            cls.clean_up_any_extra_action_data.__func__
            != ActionType.clean_up_any_extra_action_data.__func__
        )


class ActionTypeRegistry(Registry[ActionType]):
    name = "action_type"


action_scope_registry: ActionScopeRegistry = ActionScopeRegistry()
action_type_registry: ActionTypeRegistry = ActionTypeRegistry()

import dataclasses
from typing import Union, List, Tuple

from django.contrib.auth.models import AbstractUser

from baserow.contrib.database.action.scopes import TableActionScopeType
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.models import Table
from baserow.core.action.models import Action
from baserow.core.action.registries import ActionType, ActionScopeStr
from baserow.core.trash.handler import TrashHandler


class CreateFieldTypeAction(ActionType):
    type = "create_field"

    @dataclasses.dataclass
    class Params:
        field_id: int

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        table: Table,
        type_name: str,
        primary=False,
        return_updated_fields=False,
        **kwargs
    ) -> Union[Field, Tuple[Field, List[Field]]]:
        """
        Creates a new field with the given type for a table.
        See baserow.contrib.database.fields.handler.FieldHandler.create_field()
        for more information.
        Undoing this action will delete the field.
        Redoing this action will restore the field.

        :param user: The user on whose behalf the field is created.
        :param table: The table that the field belongs to.
        :param type_name: The type name of the field. Available types can be found in
            the field_type_registry.
        :param primary: Every table needs at least a primary field which cannot be
            deleted and is a representation of the whole row.
        :param return_updated_fields: When True any other fields who changed as a
            result of this field creation are returned with their new field instances.
        :param kwargs: The field values that need to be set upon creation.
        :type kwargs: object
        :return: The created field instance. If return_updated_field is set then any
            updated fields as a result of creating the field are returned in a list
            as a second tuple value.
        """

        result = FieldHandler().create_field(
            user,
            table,
            type_name,
            primary=primary,
            return_updated_fields=return_updated_fields,
            **kwargs
        )

        if return_updated_fields:
            field, updated_fields = result
        else:
            field = result
            updated_fields = None

        cls.register_action(
            user=user, params=cls.Params(field_id=field.id), scope=cls.scope(table.id)
        )

        return (field, updated_fields) if return_updated_fields else field

    @classmethod
    def scope(cls, table_id) -> ActionScopeStr:
        return TableActionScopeType.value(table_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        field = FieldHandler().get_field(params.field_id)
        FieldHandler().delete_field(user, field)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TrashHandler().restore_item(user, "field", params.field_id)


class DeleteFieldTypeAction(ActionType):
    type = "delete_field"

    @dataclasses.dataclass
    class Params:
        field_id: int

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        field: Field,
    ) -> List[Field]:
        """
        Deletes an existing field if it is not a primary field.
        See baserow.contrib.database.fields.handler.FieldHandler.delete_field()
        for more information.
        Undoing this action will restore the field.
        Redoing this action will delete the field.

        :param user: The user on whose behalf the table is created.
        :param field: The field instance that needs to be deleted.
        :return: The related updated fields.
        """

        result = FieldHandler().delete_field(user, field)

        cls.register_action(
            user=user,
            params=cls.Params(
                field.id,
            ),
            scope=cls.scope(field.table_id),
        )

        return result

    @classmethod
    def scope(cls, table_id) -> ActionScopeStr:
        return TableActionScopeType.value(table_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        TrashHandler().restore_item(user, "field", params.field_id)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        field = FieldHandler().get_field(params.field_id)
        FieldHandler().delete_field(
            user,
            field,
        )

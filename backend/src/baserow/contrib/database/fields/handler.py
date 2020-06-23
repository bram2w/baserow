import logging
from copy import deepcopy

from django.db import connections
from django.db.utils import ProgrammingError, DataError
from django.conf import settings

from baserow.core.exceptions import UserNotInGroupError
from baserow.core.utils import extract_allowed, set_allowed_attrs
from baserow.contrib.database.db.schema import lenient_schema_editor

from .exceptions import (
    PrimaryFieldAlreadyExists, CannotDeletePrimaryField, CannotChangeFieldType
)
from .registries import field_type_registry
from .models import Field


logger = logging.getLogger(__name__)


class FieldHandler:
    def create_field(self, user, table, type_name, primary=False, **kwargs):
        """
        Creates a new field with the given type for a table.

        :param user: The user on whose behalf the field is created.
        :type user: User
        :param table: The table that the field belongs to.
        :type table: Table
        :param type_name: The type name of the field. Available types can be found in
            the field_type_registry.
        :type type_name: str
        :param primary: Every table needs at least a primary field which cannot be
            deleted and is a representation of the whole row.
        :type primary: bool
        :param kwargs: The field values that need to be set upon creation.
        :type kwargs: object
        :raises UserNotInGroupError: When the user does not belong to the related group.
        :raises PrimaryFieldAlreadyExists: When we try to create a primary field,
            but one already exists.
        :return: The created field instance.
        :rtype: Field
        """

        group = table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        # Because only one primary field per table can exist and we have to check if one
        # already exists. If so the field cannot be created and an exception is raised.
        if primary and Field.objects.filter(table=table, primary=True).exists():
            raise PrimaryFieldAlreadyExists(f'A primary field already exists for the '
                                            f'table {table}.')

        # Figure out which model to use and which field types are allowed for the given
        # field type.
        field_type = field_type_registry.get(type_name)
        model_class = field_type.model_class
        allowed_fields = ['name'] + field_type.allowed_fields
        field_values = extract_allowed(kwargs, allowed_fields)
        last_order = model_class.get_last_order(table)

        instance = model_class.objects.create(table=table, order=last_order,
                                              primary=primary, **field_values)

        # Add the field to the table schema.
        connection = connections[settings.USER_TABLE_DATABASE]
        with connection.schema_editor() as schema_editor:
            to_model = table.get_model(field_ids=[], fields=[instance])
            model_field = to_model._meta.get_field(instance.db_column)
            schema_editor.add_field(to_model, model_field)

        return instance

    def update_field(self, user, field, new_type_name=None, **kwargs):
        """
        Updates the values of the given field, if provided it is also possible to change
        the type.

        :param user: The user on whose behalf the table is updated.
        :type user: User
        :param field: The field instance that needs to be updated.
        :type field: Field
        :param new_type_name: If the type needs to be changed it can be provided here.
        :type new_type_name: str
        :param kwargs: The field values that need to be updated
        :type kwargs: object
        :raises ValueError: When the provided field is not an instance of Field.
        :raises UserNotInGroupError: When the user does not belong to the related group.
        :raises CannotChangeFieldType: When the database server responds with an
            error while trying to change the field type. This should rarely happen
            because of the lenient schema editor, which replaces the value with null
            if it ould not be converted.
        :return: The updated field instance.
        :rtype: Field
        """

        if not isinstance(field, Field):
            raise ValueError('The field is not an instance of Field.')

        group = field.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        old_field = deepcopy(field)
        field_type = field_type_registry.get_by_model(field)
        from_model = field.table.get_model(field_ids=[], fields=[field])
        from_field_type = field_type.type

        # If the provided field type does not match with the current one we need to
        # migrate the field to the new type.
        if new_type_name and field_type.type != new_type_name:
            field_type = field_type_registry.get(new_type_name)
            new_model_class = field_type.model_class
            field.change_polymorphic_type_to(new_model_class)

        allowed_fields = ['name'] + field_type.allowed_fields
        field = set_allowed_attrs(kwargs, allowed_fields, field)
        field.save()

        connection = connections[settings.USER_TABLE_DATABASE]
        to_model = field.table.get_model(field_ids=[], fields=[field])
        from_model_field = from_model._meta.get_field(field.db_column)
        to_model_field = to_model._meta.get_field(field.db_column)

        # Change the field in the table schema.
        with lenient_schema_editor(
            connection,
            field_type.get_alter_column_type_function(connection, field)
        ) as schema_editor:
            try:
                schema_editor.alter_field(from_model, from_model_field, to_model_field)
            except (ProgrammingError, DataError):
                # If something is going wrong while changing the schema we will just
                # raise a specific exception. In the future we want to have some sort
                # of converter abstraction where the values of certain types can be
                # converted to another value.
                message = f'Could not alter field when changing field type ' \
                          f'{from_field_type} to {new_type_name}.'
                logger.error(message)
                raise CannotChangeFieldType(message)

        from_model_field_type = from_model_field.db_parameters(connection)['type']
        to_model_field_type = to_model_field.db_parameters(connection)['type']
        altered_column = from_model_field_type != to_model_field_type

        field_type.after_update(field, old_field, to_model, from_model, connection,
                                altered_column)

        return field

    def delete_field(self, user, field):
        """
        Deletes an existing field if it is not a primary field.

        :param user: The user on whose behalf the table is created.
        :type user: User
        :param field: The field instance that needs to be deleted.
        :type field: Field
        :raises ValueError: When the provided field is not an instance of Field.
        :raises UserNotInGroupError: When the user does not belong to the related group.
        :raises CannotDeletePrimaryField: When we try to delete the primary field
            which cannot be deleted.
        """

        if not isinstance(field, Field):
            raise ValueError('The field is not an instance of Field')

        group = field.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        if field.primary:
            raise CannotDeletePrimaryField('Cannot delete the primary field of a '
                                           'table.')

        # Remove the field from the table schema.
        connection = connections[settings.USER_TABLE_DATABASE]
        with connection.schema_editor() as schema_editor:
            from_model = field.table.get_model(field_ids=[], fields=[field])
            model_field = from_model._meta.get_field(field.db_column)
            schema_editor.remove_field(from_model, model_field)

        field.delete()

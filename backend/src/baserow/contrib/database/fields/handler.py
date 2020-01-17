from baserow.core.exceptions import UserNotInGroupError
from baserow.core.utils import extract_allowed, set_allowed_attrs

from .exceptions import PrimaryFieldAlreadyExists, CannotDeletePrimaryField
from .registries import field_type_registry
from .models import Field


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
        :return: The updated field instance.
        :rtype: Field
        """

        if not isinstance(field, Field):
            raise ValueError('The field is not an instance of Field.')

        group = field.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        # If the provided field type does not match with the current one we need to
        # migrate the field to the new type.
        field_type = field_type_registry.get_by_model(field)
        if new_type_name and field_type.type != new_type_name:
            field_type = field_type_registry.get(new_type_name)
            new_model_class = field_type.model_class
            field.change_polymorphic_type_to(new_model_class)

        allowed_fields = ['name'] + field_type.allowed_fields
        field = set_allowed_attrs(kwargs, allowed_fields, field)
        field.save()

        return field

    def delete_field(self, user, field):
        """
        Deletes an existing field if it is not a primary field.

        :param user: The user on whose behalf the table is created.
        :type user: User
        :param field: The field instance that needs to be deleted.
        :type field: Field
        """

        if not isinstance(field, Field):
            raise ValueError('The field is not an instance of Field')

        group = field.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        if field.primary:
            raise CannotDeletePrimaryField('Cannot delete the primary field of a '
                                           'table.')

        field.delete()

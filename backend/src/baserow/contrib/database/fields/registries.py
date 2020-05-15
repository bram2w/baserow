from baserow.core.registry import (
    Instance, Registry, ModelInstanceMixin, ModelRegistryMixin,
    CustomFieldsInstanceMixin, CustomFieldsRegistryMixin
)
from .exceptions import FieldTypeAlreadyRegistered, FieldTypeDoesNotExist


class FieldType(CustomFieldsInstanceMixin, ModelInstanceMixin, Instance):
    """
    This abstract class represents a custom field type that can be added to the
    field type registry. It must be extended so customisation can be done. Each field
    type will have his own model that must extend the Field model, this is needed so
    that the user can set custom settings per field instance he has created.

    Example:
        from baserow.contrib.database.fields.models import Field
        from baserow.contrib.database.fields.registry import (
            FieldType, field_type_registry
        )

        class ExampleFieldModel(FieldType):
            pass

        class ExampleFieldType(FieldType):
            type = 'a-unique-field-type-name'
            model_class = ExampleFieldModel
            allowed_fields = ['text_default']
            serializer_field_names = ['text_default']
            serializer_field_overrides = {
                'text_default': serializers.CharField()
            }

        field_type_registry.register(ExampleFieldType())
    """

    def prepare_value_for_db(self, instance, value):
        """
        When a row is created or updated all the values are going to be prepared for the
        database. The value for this field type will run through this method and the
        returned value will be used. It is also possible to raise validation errors if
        the value is incorrect.

        :param instance: The field instance.
        :type instance: Field
        :param value: The value that needs to be inserted or updated.
        :type value: str
        :return: The modified value that is going to be saved in the database.
        :rtype: str
        """

        return value

    def get_serializer_field(self, instance, **kwargs):
        """
        Should return the serializer field based on the custom model instance
        attributes. It is common that the field is not required so that a user
        doesn't have to update the field each time another field in the same row
        changes.

        :param instance: The field instance for which to get the model field for.
        :type instance: Field
        :param kwargs: The kwargs that will be passed to the field.
        :type kwargs: dict
        :return: The serializer field that represents the field instance attributes.
        :rtype: serializer.Field
        """

        raise NotImplementedError('Each must have his own get_serializer_field method.')

    def get_model_field(self, instance, **kwargs):
        """
        Should return the model field based on the custom model instance attributes. It
        is common that the field can be blank because people are going to create a row
        without any data in it.

        :param instance: The field instance for which to get the model field for.
        :type instance: Field
        :param kwargs: The kwargs that will be passed to the field.
        :type kwargs: dict
        :return: The model field that represents the field instance attributes.
        :rtype: model.Field
        """

        raise NotImplementedError('Each must have his own get_model_field method.')

    def random_value(self, instance, fake):
        """
        Should return a random value that can be used as value for the field. This is
        used by the fill_table management command which will add an N amount of rows
        to the a table with random data.

        :param instance: The field instance for which to get the random value for.
        :type instance: Field
        :param fake: An instance of the Faker package.
        :type fake: Faker
        :return: The randomly generated value.
        :rtype: any
        """

        return None

    def get_alter_column_type_function(self, connection, instance):
        """
        Can optionally return a SQL function as string to convert the old field's value
        when changing the field type. If None is returned no function will be
        applied. The connection can be used to see which engine is used, postgresql,
        mysql or sqlite.

        Example when a string is converted to a number, the function could be:
        REGEXP_REPLACE(p_in, '[^0-9]', '', 'g') which would remove all non numeric
        characters. The p_in variable is the old value as a string.

        :param connection: The used connection. This can for example be used to check
            the database engine type.
        :type connection: DatabaseWrapper
        :param instance: The new field instance.
        :type instance: Field
        :return: The SQL function to convert the value.
        :rtype: None or str
        """

        return None

    def after_update(self, field, old_field, model, old_model, connection,
                     altered_column):
        """
        This hook is called right after a field has been updated. In some cases data
        mutation still has to be done in order to maintain data integrity. For example
        when the only the allowing of negative values has been changed for the number
        field.

        :param field: The updated field instance.
        :type: field Field
        :param old_field: The old field instance. It is not recommended to call the
            save function as this will undo part of the changes that have been made.
            This is just for comparing values.
        :type old_field: Field
        :param model: The generated model containing only the new field.
        :type model: Model
        :param old_model: The old generated model containing only the old field.
        :type old_model: Model
        :param connection: The connection used to make the database schema change.
        :type connection: DatabaseWrapper
        :param altered_column: Indicates whether the column has been altered in the
            table. Sometimes data has to be updated if the column hasn't been altered.
        :type altered_column: bool
        """


class FieldTypeRegistry(CustomFieldsRegistryMixin, ModelRegistryMixin, Registry):
    """
    With the field type registry it is possible to register new field types.  A field
    type is an abstraction made specifically for Baserow. If added to the registry a
    user can create new fields based on this type.
    """

    name = 'field'
    does_not_exist_exception_class = FieldTypeDoesNotExist
    already_registered_exception_class = FieldTypeAlreadyRegistered


# A default field type registry is created here, this is the one that is used
# throughout the whole Baserow application to add a new field type.
field_type_registry = FieldTypeRegistry()

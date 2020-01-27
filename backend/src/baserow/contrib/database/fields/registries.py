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

    def get_model_field(self, instance, **kwargs):
        """
        Should return the model field based on the custom model instance attributes.

        :param instance: The field instance for which to get the model field for.
        :type instance: Field
        :param kwargs: The kwargs that will be passed to the field.
        :type kwargs: dict
        :return: The modal field that represents the field instance attributes.
        :rtype: Field
        """
        raise NotImplementedError('Each must have his own get_model_field method.')


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

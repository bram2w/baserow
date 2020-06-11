from rest_framework import serializers

from baserow.api.v0.utils import get_serializer_class


class RowSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id',)
        extra_kwargs = {
            'id': {
                'read_only': True
            }
        }


def get_row_serializer_class(model, base_class=None):
    """
    Generates a Django rest framework model serializer based on the available fields
    that belong to this model. For each table field, used to generate this serializer,
    a serializer field will be added via the `get_serializer_field` method of the field
    type.

    :param model: The model for which to generate a serializer.
    :type model: Model
    :param base_class: The base serializer class that will be extended when
        generating the serializer. By default this is a regular ModelSerializer.
    :type base_class: ModelSerializer
    :return: The generated serializer.
    :rtype: ModelSerializer
    """

    field_objects = model._field_objects
    field_names = [field['name'] for field in field_objects.values()]
    field_overrides = {
        field['name']: field['type'].get_serializer_field(field['field'])
        for field in field_objects.values()
    }
    return get_serializer_class(model, field_names, field_overrides, base_class)

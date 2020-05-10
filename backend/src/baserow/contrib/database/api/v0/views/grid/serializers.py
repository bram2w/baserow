from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from baserow.contrib.database.views.models import GridView, GridViewFieldOptions


class GridViewFieldOptionsField(serializers.Field):
    default_error_messages = {
        'invalid_key': _('Field option key must be numeric.'),
        'invalid_value': _('Must be valid field options.')
    }

    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = False
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        """
        This method only validates if the provided data dict is in the correct
        format. Not if the field id actually exists.

        Example format:
        {
            FIELD_ID: {
                width: 200
            }
        }

        :param data: The data that needs to be validated.
        :type data: dict
        :return: The validated dict.
        :rtype: dict
        """

        internal = {}
        for key, value in data.items():
            if not (
                isinstance(key, int) or (isinstance(key, str) and key.isnumeric())
            ):
                self.fail('invalid_key')
            serializer = GridViewFieldOptionsSerializer(data=value)
            if not serializer.is_valid():
                self.fail('invalid_value')
            internal[int(key)] = serializer.data
        return internal

    def to_representation(self, value):
        """
        If the provided value is a GridView instance we need to fetch the options from
        the database. We can easily use the `get_field_options` of the GridView for
        that and format the dict the way we want.

        If the provided value is a dict it means the field options have already been
        provided and validated once, so we can just return that value. The variant is
        used when we want to validate the input.

        :param value: The prepared value that needs to be serialized.
        :type value: GridView or dict
        :return: A dictionary containing the
        :rtype: dict
        """

        if isinstance(value, GridView):
            # If the fields are in the context we can pass them into the
            # `get_field_options` call so that they don't have to be fetched from the
            # database again.
            fields = self.context.get('fields')
            return {
                field_options.field_id:
                    GridViewFieldOptionsSerializer(field_options).data
                for field_options in value.get_field_options(True, fields)
            }
        else:
            return value


class GridViewSerializer(serializers.ModelSerializer):
    field_options = GridViewFieldOptionsField(required=False)

    class Meta:
        model = GridView
        fields = ('field_options',)


class GridViewFieldOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GridViewFieldOptions
        fields = ('width',)

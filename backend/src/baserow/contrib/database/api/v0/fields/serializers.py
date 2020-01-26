from django.utils.functional import lazy

from rest_framework import serializers

from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.models import Field


class FieldSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = Field
        fields = ('id', 'name', 'order', 'type', 'primary')
        extra_kwargs = {
            'id': {
                'read_only': True
            }
        }

    def get_type(self, instance):
        # It could be that the field related to the instance is already in the context
        # else we can call the specific_class property to find it.
        field = self.context.get('instance_type')

        if not field:
            field = field_type_registry.get_by_model(instance.specific_class)

        return field.type


class CreateFieldSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=lazy(field_type_registry.get_types, list)(),
                                   required=True)

    class Meta:
        model = Field
        fields = ('name', 'type')


class UpdateFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ('name',)
        extra_kwargs = {
            'name': {'required': False}
        }

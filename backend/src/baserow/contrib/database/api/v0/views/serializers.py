from django.utils.functional import lazy

from rest_framework import serializers

from baserow.contrib.database.api.v0.serializers import TableSerializer
from baserow.contrib.database.views.registries import view_type_registry
from baserow.contrib.database.views.models import View


class ViewSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    table = TableSerializer()

    class Meta:
        model = View
        fields = ('id', 'name', 'order', 'type', 'table')
        extra_kwargs = {
            'id': {
                'read_only': True
            }
        }

    def get_type(self, instance):
        # It could be that the view related to the instance is already in the context
        # else we can call the specific_class property to find it.
        view = self.context.get('instance_type')
        if not view:
            view = view_type_registry.get_by_model(instance.specific_class)

        return view.type


class CreateViewSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=lazy(view_type_registry.get_types, list)())

    class Meta:
        model = View
        fields = ('name', 'type')


class UpdateViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = View
        fields = ('name',)
        extra_kwargs = {
            'name': {'required': False}
        }

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
        view = self.context.get('view')
        if not view:
            view = view_type_registry.get_by_model(instance.specific_class)

        return view.type


class ViewCreateSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=lazy(view_type_registry.get_types, list)())

    class Meta:
        model = View
        fields = ('name', 'type')


class ViewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = View
        fields = ('name',)


def get_view_serializer(instance, **kwargs):
    """
    Returns an instantiated serializer based on the instance class type. Custom
    serializers can be defined per view type. This function will return the one that is
    set else it will return the default one.

    :param instance: The instance where a serializer is needed for.
    :type instance: View
    :return: An instantiated serializer for the instance.
    :rtype: ViewSerializer
    """
    view = view_type_registry.get_by_model(instance.specific_class)
    serializer_class = view.instance_serializer_class

    if not serializer_class:
        serializer_class = ViewSerializer

    return serializer_class(instance, context={'view': view}, **kwargs)

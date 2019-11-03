from django.utils.functional import lazy

from rest_framework import serializers

from baserow.api.v0.groups.serializers import GroupSerializer
from baserow.core.applications import registry
from baserow.core.models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    group = GroupSerializer()

    class Meta:
        model = Application
        fields = ('id', 'name', 'order', 'type', 'group')
        extra_kwargs = {
            'id': {
                'read_only': True
            }
        }

    def get_type(self, instance):
        # It could be that the application related to the instance is already in the
        # context else we can call the specific_class property to find it.
        application = self.context.get('application')
        if not application:
            application = registry.get_by_model(instance.specific_class)

        return application.type


class ApplicationCreateSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=lazy(registry.get_types, list)())

    class Meta:
        model = Application
        fields = ('name', 'type')


class ApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ('name',)


def get_application_serializer(instance, **kwargs):
    """
    Returns an instantiated serialized based on the instance class type. Custom
    serializers can be defined per application. This function will return that one is
    set else it will return the default one.

    :param instance: The instance where a serializer is needed for.
    :type instance: Application
    :return: An instantiated serializer for the instance.
    :rtype: ApplicationSerializer
    """
    application = registry.get_by_model(instance.specific_class)
    serializer_class = application.instance_serializer

    if not serializer_class:
        serializer_class = ApplicationSerializer

    return serializer_class(instance, context={'application': application}, **kwargs)

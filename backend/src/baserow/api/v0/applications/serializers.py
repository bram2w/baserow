from rest_framework import serializers

from baserow.core.applications import registry
from baserow.core.models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = ('id', 'name', 'order', 'type')
        extra_kwargs = {
            'id': {
                'read_only': True
            }
        }

    def get_type(self, instance):
        application = registry.get_by_model(instance.specific_class)
        return application.type


class ApplicationCreateSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=registry.get_types())

    class Meta:
        model = Application
        fields = ('name', 'type')


class ApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ('name',)

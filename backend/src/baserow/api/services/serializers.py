from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.core.services.models import Service
from baserow.core.services.registries import service_type_registry


class ServiceSerializer(serializers.ModelSerializer):
    """
    Basic service serializer mostly for returned values.
    """

    type = serializers.SerializerMethodField(help_text="The type of the service.")

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        return service_type_registry.get_by_model(instance.specific_class).type

    class Meta:
        model = Service
        fields = ("id", "integration_id", "type")
        extra_kwargs = {
            "id": {"read_only": True},
            "integration_id": {"read_only": True},
            "type": {"read_only": True},
        }


class PublicServiceSerializer(serializers.ModelSerializer):
    """
    Basic service serializer mostly for public returned values.
    Don't add sensitive data here.
    """

    type = serializers.SerializerMethodField(help_text="The type of the service.")

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        return service_type_registry.get_by_model(instance.specific_class).type

    class Meta:
        model = Service
        fields = ("id", "type")
        extra_kwargs = {
            "id": {"read_only": True},
            "type": {"read_only": True},
        }


class CreateServiceSerializer(serializers.ModelSerializer):
    """
    This serializer allow to set the type of a service and the service id before which
    we want to insert the new service.
    """

    type = serializers.ChoiceField(
        choices=lazy(service_type_registry.get_types, list)(),
        required=True,
        help_text="The type of the service.",
    )

    class Meta:
        model = Service
        fields = ("type",)


class UpdateServiceSerializer(serializers.ModelSerializer):
    integration_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="The related integration id.",
    )

    class Meta:
        model = Service
        fields = ("integration_id",)

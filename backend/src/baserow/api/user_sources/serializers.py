from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.core.user_sources.models import UserSource
from baserow.core.user_sources.registries import user_source_type_registry


class UserSourceSerializer(serializers.ModelSerializer):
    """
    Basic user_source serializer mostly for returned values.
    """

    type = serializers.SerializerMethodField(help_text="The type of the user_source.")

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        return user_source_type_registry.get_by_model(instance.specific_class).type

    class Meta:
        model = UserSource
        fields = ("id", "application_id", "integration_id", "type", "name", "order")
        extra_kwargs = {
            "id": {"read_only": True},
            "application_id": {"read_only": True},
            "integration_id": {"read_only": True},
            "type": {"read_only": True},
            "name": {"read_only": True},
            "order": {"read_only": True, "help_text": "Lowest first."},
        }


class CreateUserSourceSerializer(serializers.ModelSerializer):
    """
    This serializer allow to set the type of an user_source and the user_source id
    before which we want to insert the new user_source.
    """

    type = serializers.ChoiceField(
        choices=lazy(user_source_type_registry.get_types, list)(),
        required=True,
        help_text="The type of the user_source.",
    )
    before_id = serializers.IntegerField(
        required=False,
        help_text="If provided, creates the user_source before the user_source with "
        "the given id.",
    )
    integration_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="The related integration id.",
    )

    class Meta:
        model = UserSource
        fields = ("before_id", "type", "name", "integration_id")


class UpdateUserSourceSerializer(serializers.ModelSerializer):
    integration_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="The related integration id.",
    )

    class Meta:
        model = UserSource
        fields = ("name", "integration_id")
        extra_kwargs = {
            "name": {"required": False},
            "integration_id": {"required": False},
        }


class MoveUserSourceSerializer(serializers.Serializer):
    before_id = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text=(
            "If provided, the user_source is moved before the user_source with this Id. "
            "Otherwise the user_source is placed at the end of the page."
        ),
    )

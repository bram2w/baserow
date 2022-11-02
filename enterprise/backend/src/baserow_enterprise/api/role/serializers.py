from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from jsonschema import ValidationError
from rest_framework import serializers

from baserow.api.serializers import NaturalKeyRelatedField
from baserow.core.registries import object_scope_type_registry
from baserow_enterprise.models import Role, RoleAssignment
from baserow_enterprise.role.handler import USER_TYPE

User = get_user_model()


class SubjectTypeField(serializers.ChoiceField):
    """
    A field to automatically get the subject ContentType.
    """

    def to_representation(self, value):
        # Value is a content_type
        if value.model_class() == User:
            return USER_TYPE
        else:
            raise ValidationError(f"This subject content type is not supported")

    def to_internal_value(self, data):
        # Data is a subject_type name
        if data == USER_TYPE:
            return ContentType.objects.get_by_natural_key("auth", "user")
        else:
            raise ValidationError(f"The subject type {data} is not supported")


class ScopeTypeField(serializers.ChoiceField):
    """
    A field to automatically get the scope ContentType object.
    """

    def to_representation(self, value):
        # Value is a content_type
        scope_type = object_scope_type_registry.get_by_model(value.model_class())
        return scope_type.type

    def to_internal_value(self, data):
        # Data is a scope_type name
        scope_type = object_scope_type_registry.get(data)
        return ContentType.objects.get_for_model(scope_type.model_class)


@extend_schema_field(OpenApiTypes.STR)
class RoleField(NaturalKeyRelatedField):
    pass


class CreateRoleAssignmentSerializer(serializers.Serializer):
    """
    The create role assignment serializer.
    """

    subject_id = serializers.IntegerField(
        min_value=1,
        help_text="The subject ID. A subject is an actor that can do operations.",
    )
    subject_type = SubjectTypeField(
        help_text="The subject type.",
        choices=[USER_TYPE],
    )

    role = RoleField(
        model=Role,
        required=False,
        allow_null=True,
        help_text=(
            "The uid of the role you want to assign to the user in given group. "
            "You can omit this property if you want to remove the role."
        ),
    )

    scope_id = serializers.IntegerField(
        min_value=1,
        help_text=(
            "The ID of the scope object. The scope object limit the role "
            "assignment to this scope and all it's descendants."
        ),
    )
    scope_type = ScopeTypeField(
        help_text="The scope object type.",
        choices=lazy(object_scope_type_registry.get_types, list)(),
    )

    def to_internal_value(self, data):
        """
        Populate the scope and the subject with the actual object.
        """

        result = super().to_internal_value(data)
        # Populate scope and subject with real object
        result["scope"] = result["scope_type"].get_object_for_this_type(
            id=result["scope_id"]
        )
        result["subject"] = result["subject_type"].get_object_for_this_type(
            id=result["subject_id"]
        )
        return result


class RoleAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for RoleAssignment used for response.
    """

    subject_type = SubjectTypeField(
        choices=[USER_TYPE],
        help_text="The subject type.",
    )
    scope_type = ScopeTypeField(
        help_text=(
            "The ID of the scope object. The scope object limit the role "
            "assignment to this scope and all it's descendants."
        ),
        choices=lazy(object_scope_type_registry.get_types, list)(),
    )
    role = RoleField(
        model=Role,
        help_text=("The uid of the role assigned to the user in the given group."),
    )

    class Meta:
        model = RoleAssignment
        fields = (
            "id",
            "role",
            "subject_id",
            "scope_id",
            "subject_type",
            "scope_type",
        )

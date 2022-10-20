from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from baserow_enterprise.models import Role, RoleAssignment
from jsonschema import ValidationError
from rest_framework import serializers

from baserow.core.registries import object_scope_type_registry

User = get_user_model()


class NaturalKeyRelatedField(serializers.ListField):
    def __init__(self, model=None, **kwargs):
        self._model = model
        super().__init__(**kwargs)

    def to_representation(self, value):

        representation = super().to_representation(value.natural_key())

        if len(representation) == 1:
            return representation[0]
        else:
            return representation

    def to_internal_value(self, data):
        if not isinstance(data, list):
            data = [data]

        natural_key = super().to_internal_value(data)
        return self._model.objects.get_by_natural_key(*natural_key)


class SubjectTypeField(serializers.Field):
    def to_representation(self, value):
        # Value is a content_type
        if value.model_class() == User:
            return "user"
        else:
            raise ValidationError(f"This subject content type is not supported")

    def to_internal_value(self, data):
        # Data is a subject_type name
        if data == "user":
            return ContentType.objects.get_by_natural_key("auth", "user")
        else:
            raise ValidationError(f"The subject type {data} is not supported")


class ScopeTypeField(serializers.Field):
    def to_representation(self, value):
        # Value is a content_type
        scope_type = object_scope_type_registry.get_by_model(value.model_class())
        return scope_type.type

    def to_internal_value(self, data):
        # Data is a scope_type name
        scope_type = object_scope_type_registry.get(data)
        return ContentType.objects.get_for_model(scope_type.model_class)


class CreateRoleAssignmentSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField(min_value=1)
    subject_type = SubjectTypeField()

    role = NaturalKeyRelatedField(model=Role, required=False, allow_null=True)

    scope_id = serializers.IntegerField(min_value=1)
    scope_type = ScopeTypeField()

    def to_internal_value(self, data):
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
    subject_type = SubjectTypeField()
    scope_type = ScopeTypeField()
    role = NaturalKeyRelatedField(model=Role)

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

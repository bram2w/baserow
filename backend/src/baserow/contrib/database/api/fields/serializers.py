from datetime import timedelta
from typing import Optional

from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.serializers import SkipField, empty

from baserow.api.user_files.serializers import UserFileURLAndThumbnailsSerializerMixin
from baserow.api.user_files.validators import user_file_name_validator
from baserow.contrib.database.fields.constants import (
    BASEROW_BOOLEAN_FIELD_FALSE_VALUES,
    BASEROW_BOOLEAN_FIELD_TRUE_VALUES,
)
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.utils.duration import prepare_duration_value_for_db
from baserow.core.utils import split_comma_separated_string


class FieldSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField(help_text="The type of the related field.")
    read_only = serializers.SerializerMethodField(
        help_text="Indicates whether the field is a read only field. If true, "
        "it's not possible to update the cell value."
    )

    class Meta:
        model = Field
        fields = ("id", "table_id", "name", "order", "type", "primary", "read_only")
        extra_kwargs = {
            "id": {"read_only": True},
            "table_id": {"read_only": True},
        }

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        return field_type_registry.get_by_model(instance.specific_class).type

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_read_only(self, instance):
        return field_type_registry.get_by_model(instance.specific_class).read_only


class RelatedFieldsSerializer(serializers.Serializer):
    related_fields = serializers.SerializerMethodField(
        help_text="A list of related fields which also changed.",
    )

    def __init__(self, *args, **kwargs):
        self.related_fields_list = kwargs.pop("related_fields", [])
        super().__init__(*args, **kwargs)

    @extend_schema_field(FieldSerializer(many=True))
    def get_related_fields(self, instance):
        return [
            field_type_registry.get_serializer(f, FieldSerializer).data
            for f in self.related_fields_list
        ]


class FieldSerializerWithRelatedFields(FieldSerializer, RelatedFieldsSerializer):
    class Meta(FieldSerializer.Meta):
        fields = FieldSerializer.Meta.fields + ("related_fields",)


class SelectOptionSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    value = serializers.CharField(max_length=255, required=True)
    color = serializers.CharField(max_length=255, required=True)


class CreateFieldSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=lazy(field_type_registry.get_types, list)(), required=True
    )

    class Meta:
        model = Field
        fields = ("name", "type")


class UpdateFieldSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=lazy(field_type_registry.get_types, list)(), required=False
    )

    class Meta:
        model = Field
        fields = ("name", "type")
        extra_kwargs = {
            "name": {"required": False},
        }


class ArrayValueSerializer(serializers.Serializer):
    id = serializers.IntegerField(
        read_only=True,
        required=False,
        help_text="The id of the row this value was looked up from.",
    )
    ids = serializers.DictField(
        child=serializers.IntegerField(
            read_only=True,
            required=False,
            help_text="The id of the row the value ultimately came from or the link "
            "row ids which led to the value.",
        ),
        read_only=True,
        required=False,
        help_text="If this value is a lookup crossing multiple link fields each link "
        "row id involved will be set in here.",
    )

    def __init__(self, child, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["value"] = child

    def to_representation(self, instance):
        return super().to_representation(instance)


class LinkRowValueSerializer(serializers.Serializer):
    id = serializers.IntegerField(
        read_only=True,
        help_text="The unique identifier of the row in the related table.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["value"] = serializers.CharField(
            help_text="The primary field's value as a string of the row in the "
            "related table.",
            required=False,
            source="*",
        )


class FileFieldRequestSerializer(serializers.Serializer):
    visible_name = serializers.CharField(
        required=False, help_text="A visually editable name for the field."
    )
    name = serializers.CharField(
        required=True,
        validators=[user_file_name_validator],
        help_text="Accepts the name of the already uploaded user file.",
    )

    def validate(self, data):
        if "name" not in data:
            raise serializers.ValidationError(
                {"name": "This field is required."}, code="required"
            )
        return data


class FileFieldResponseSerializer(
    UserFileURLAndThumbnailsSerializerMixin, serializers.Serializer
):
    visible_name = serializers.CharField()
    name = serializers.CharField()
    size = serializers.IntegerField()
    mime_type = serializers.CharField()
    is_image = serializers.BooleanField()
    image_width = serializers.IntegerField()
    image_height = serializers.IntegerField()
    uploaded_at = serializers.DateTimeField()

    def get_instance_attr(self, instance, name):
        return instance[name]


@extend_schema_field(OpenApiTypes.NONE)
class MustBeEmptyField(serializers.Field):
    def __init__(self, error_message, *args, **kwargs):
        def validator(value):
            raise ValidationError(error_message, code="invalid")

        kwargs["write_only"] = True
        kwargs["required"] = False
        kwargs["validators"] = [validator]
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        return None


class UniqueRowValueParamsSerializer(serializers.Serializer):
    limit = serializers.IntegerField(
        required=False, help_text="Defines how many values should be returned."
    )
    split_comma_separated = serializers.BooleanField(
        required=False,
        help_text="Indicates whether the original column values must be splitted by "
        "comma.",
        default=False,
    )


class UniqueRowValuesSerializer(serializers.Serializer):
    values = serializers.ListSerializer(child=serializers.CharField())


class CollaboratorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(source="first_name", read_only=True)


class DuplicateFieldParamsSerializer(serializers.Serializer):
    duplicate_data = serializers.BooleanField(
        default=False, help_text="Indicates whether the data should be duplicated."
    )


class ListOrStringField(serializers.ListField):
    """
    A serializer field that accept a List or a CSV string that will be converted to
    an Array.
    """

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = split_comma_separated_string(data)

        return super().to_internal_value(data)


@extend_schema_field(OpenApiTypes.INT)
class IntegerOrStringField(serializers.Field):
    """
    A serializer field that accept an int or a string.
    """

    def __init__(self, **kwargs):
        required = kwargs.pop("required", False)
        allow_null = kwargs.pop("allow_null", True)
        allow_blank = kwargs.pop("allow_blank", allow_null)
        min_value = kwargs.pop("min_value", None)
        max_value = kwargs.pop("max_value", None)
        max_length = kwargs.pop("max_length", None)

        super().__init__(required=required, allow_null=allow_null, **kwargs)
        self._integer_field = serializers.IntegerField(
            **{
                "required": required,
                "allow_null": allow_null,
                "min_value": min_value,
                "max_value": max_value,
                **kwargs,
            }
        )
        self._char_field = serializers.CharField(
            **{
                "required": required,
                "allow_blank": allow_blank,
                "max_length": max_length,
                **kwargs,
            }
        )

    def to_internal_value(self, data):
        if isinstance(data, int) or data is None:
            return self._integer_field.to_internal_value(data)
        elif isinstance(data, str):
            return self._char_field.to_internal_value(data)
        else:
            raise serializers.ValidationError(
                "The provided value should be a valid integer or string",
                code="invalid",
            )

    def to_representation(self, value):
        return value


class BaserowBooleanField(serializers.BooleanField):
    """
    A Baserow specific `BooleanField` that extends the `TRUE_VALUES` and
    `FALSE_VALUES` in DRF so that we support "checked" and "unchecked".
    """

    TRUE_VALUES = BASEROW_BOOLEAN_FIELD_TRUE_VALUES
    FALSE_VALUES = BASEROW_BOOLEAN_FIELD_FALSE_VALUES


@extend_schema_field(OpenApiTypes.FLOAT)
class DurationFieldSerializer(serializers.Field):
    """
    A serializer field that accept a float or a string and return a timedelta.
    """

    def __init__(self, duration_format, **kwargs):
        self.duration_format = duration_format
        super().__init__(**kwargs)

    def to_internal_value(self, data) -> Optional[timedelta]:
        return prepare_duration_value_for_db(
            data, self.duration_format, serializers.ValidationError
        )

    def to_representation(self, value):
        if isinstance(value, (int, float)):
            # Durations are stored as the number of seconds for lookups/arrays in
            # formula land, so just return the value in that case.
            return value
        else:
            return value.total_seconds()


class PasswordSerializer(serializers.CharField):
    def run_validation(self, data=empty):
        if isinstance(data, bool) and data:
            raise SkipField()
        return super().run_validation(data=data)

    def to_internal_value(self, data) -> Optional[str]:
        if data is None or data == "":
            return None

        return make_password(data)

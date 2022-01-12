from django.utils.functional import lazy
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.api.user_files.serializers import (
    UserFileURLAndThumbnailsSerializerMixin,
)
from baserow.api.user_files.validators import user_file_name_validator
from baserow.contrib.database.api.views.serializers import (
    ViewSortSerializer,
    ViewFilterSerializer,
)
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.registries import field_type_registry


class FieldSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField(help_text="The type of the related field.")

    class Meta:
        model = Field
        fields = ("id", "table_id", "name", "order", "type", "primary")
        extra_kwargs = {
            "id": {"read_only": True},
            "table_id": {"read_only": True},
        }

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        # It could be that the field related to the instance is already in the context
        # else we can call the specific_class property to find it.
        field = self.context.get("instance_type")

        if not field:
            field = field_type_registry.get_by_model(instance.specific_class)

        return field.type


class FieldWithFiltersAndSortsSerializer(FieldSerializer):
    filters = ViewFilterSerializer(many=True, source="viewfilter_set")
    sortings = ViewSortSerializer(many=True, source="viewsort_set")

    class Meta(FieldSerializer.Meta):
        fields = FieldSerializer.Meta.fields + (
            "filters",
            "sortings",
        )


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

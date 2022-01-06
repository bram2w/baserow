from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.api.fields.serializers import FieldSerializer
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.views.models import GridViewFieldOptions, ViewSort, View
from baserow.contrib.database.views.registries import view_type_registry


class GridViewFieldOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GridViewFieldOptions
        fields = ("width", "hidden", "order")


class GridViewFilterSerializer(serializers.Serializer):
    field_ids = serializers.ListField(
        allow_empty=False,
        required=False,
        default=None,
        child=serializers.IntegerField(),
        help_text="Only the fields related to the provided ids are added to the "
        "response. If None are provided all fields will be returned.",
    )
    row_ids = serializers.ListField(
        allow_empty=False,
        child=serializers.IntegerField(),
        help_text="Only rows related to the provided ids are added to the response.",
    )


class PublicViewSortSerializer(serializers.ModelSerializer):
    view = serializers.SlugField(source="view.slug")

    class Meta:
        model = ViewSort
        fields = ("id", "view", "field", "order")
        extra_kwargs = {"id": {"read_only": True}}


class PublicGridViewTableSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    database_id = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.INT)
    def get_id(self, instance):
        return PUBLIC_PLACEHOLDER_ENTITY_ID

    @extend_schema_field(OpenApiTypes.INT)
    def get_database_id(self, instance):
        return PUBLIC_PLACEHOLDER_ENTITY_ID


class PublicGridViewSerializer(serializers.ModelSerializer):
    id = serializers.SlugField(source="slug")
    table = PublicGridViewTableSerializer()
    type = serializers.SerializerMethodField()
    sortings = serializers.SerializerMethodField()

    @extend_schema_field(PublicViewSortSerializer(many=True))
    def get_sortings(self, instance):
        sortings = PublicViewSortSerializer(
            instance=instance.viewsort_set.filter(field__in=self.context["fields"]),
            many=True,
        )
        return sortings.data

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        # It could be that the view related to the instance is already in the context
        # else we can call the specific_class property to find it.
        view = self.context.get("instance_type")
        if not view:
            view = view_type_registry.get_by_model(instance.specific_class)

        return view.type

    class Meta:
        model = View
        fields = (
            "id",
            "table",
            "name",
            "order",
            "type",
            "sortings",
            "public",
            "slug",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "slug": {"read_only": True},
        }


class PublicFieldSerializer(FieldSerializer):
    table_id = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.INT)
    def get_table_id(self, instance):
        return PUBLIC_PLACEHOLDER_ENTITY_ID


class PublicGridViewInfoSerializer(serializers.Serializer):
    # get_fields is an actual method on serializers.Serializer so we can't override it.
    fields = serializers.SerializerMethodField(method_name="get_public_fields")
    view = serializers.SerializerMethodField()

    # @TODO show correct API docs discriminated by field type.
    @extend_schema_field(PublicFieldSerializer(many=True))
    def get_public_fields(self, instance):
        return [
            field_type_registry.get_serializer(field, PublicFieldSerializer).data
            for field in self.context["fields"]
        ]

    # @TODO show correct API docs discriminated by field type.
    @extend_schema_field(PublicGridViewSerializer)
    def get_view(self, instance):
        return view_type_registry.get_serializer(
            instance, PublicGridViewSerializer, context=self.context
        ).data

    def __init__(self, *args, **kwargs):
        kwargs["context"] = kwargs.get("context", {})
        kwargs["context"]["fields"] = kwargs.pop("fields", [])
        super().__init__(instance=kwargs.pop("view", None), *args, **kwargs)

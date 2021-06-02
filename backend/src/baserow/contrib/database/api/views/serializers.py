from django.utils.functional import lazy

from drf_spectacular.utils import extend_schema_field
from drf_spectacular.openapi import OpenApiTypes

from rest_framework import serializers

from baserow.contrib.database.api.serializers import TableSerializer
from baserow.contrib.database.views.registries import (
    view_type_registry,
    view_filter_type_registry,
)
from baserow.contrib.database.views.models import View, ViewFilter, ViewSort


class ViewFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewFilter
        fields = ("id", "view", "field", "type", "value")
        extra_kwargs = {"id": {"read_only": True}}


class CreateViewFilterSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=lazy(view_filter_type_registry.get_types, list)(),
        help_text=ViewFilter._meta.get_field("type").help_text,
    )

    class Meta:
        model = ViewFilter
        fields = ("field", "type", "value")
        extra_kwargs = {"value": {"default": ""}}


class UpdateViewFilterSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=lazy(view_filter_type_registry.get_types, list)(),
        required=False,
        help_text=ViewFilter._meta.get_field("type").help_text,
    )

    class Meta(CreateViewFilterSerializer.Meta):
        model = ViewFilter
        fields = ("field", "type", "value")
        extra_kwargs = {"field": {"required": False}, "value": {"required": False}}


class ViewSortSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewSort
        fields = ("id", "view", "field", "order")
        extra_kwargs = {"id": {"read_only": True}}


class CreateViewSortSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewSort
        fields = ("field", "order")
        extra_kwargs = {
            "order": {"default": ViewSort._meta.get_field("order").default},
        }


class UpdateViewSortSerializer(serializers.ModelSerializer):
    class Meta(CreateViewFilterSerializer.Meta):
        model = ViewSort
        fields = ("field", "order")
        extra_kwargs = {"field": {"required": False}, "order": {"required": False}}


class ViewSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    table = TableSerializer()
    filters = ViewFilterSerializer(many=True, source="viewfilter_set", required=False)
    sortings = ViewSortSerializer(many=True, source="viewsort_set", required=False)

    class Meta:
        model = View
        fields = (
            "id",
            "table_id",
            "name",
            "order",
            "type",
            "table",
            "filter_type",
            "filters",
            "sortings",
            "filters_disabled",
        )
        extra_kwargs = {"id": {"read_only": True}, "table_id": {"read_only": True}}

    def __init__(self, *args, **kwargs):
        context = kwargs.setdefault("context", {})
        context["include_filters"] = kwargs.pop("filters", False)
        context["include_sortings"] = kwargs.pop("sortings", False)
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        # We remove the fields in to_representation rather than __init__ as otherwise
        # drf-spectacular will not know that filters and sortings exist as optional
        # return fields. This way the fields are still dynamic and also show up in the
        # OpenAPI specification.
        if not self.context["include_filters"]:
            self.fields.pop("filters", None)

        if not self.context["include_sortings"]:
            self.fields.pop("sortings", None)

        return super().to_representation(instance)

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        # It could be that the view related to the instance is already in the context
        # else we can call the specific_class property to find it.
        view = self.context.get("instance_type")
        if not view:
            view = view_type_registry.get_by_model(instance.specific_class)

        return view.type


class CreateViewSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=lazy(view_type_registry.get_types, list)())

    class Meta:
        model = View
        fields = ("name", "type", "filter_type", "filters_disabled")


class UpdateViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = View
        fields = ("name", "filter_type", "filters_disabled")
        extra_kwargs = {
            "name": {"required": False},
            "filter_type": {"required": False},
            "filters_disabled": {"required": False},
        }


class OrderViewsSerializer(serializers.Serializer):
    view_ids = serializers.ListField(
        child=serializers.IntegerField(), help_text="View ids in the desired order."
    )

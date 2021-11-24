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


class FieldOptionsField(serializers.Field):
    default_error_messages = {
        "invalid_key": "Field option key must be numeric.",
        "invalid_value": "Must be valid field options.",
    }

    def __init__(self, serializer_class, **kwargs):
        self.serializer_class = serializer_class
        self._spectacular_annotation = {
            "field": serializers.DictField(
                child=serializer_class(),
                help_text="An object containing the field id as key and the properties "
                "related to view as value.",
            )
        }
        kwargs["source"] = "*"
        kwargs["read_only"] = False
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        """
        This method only passes the validation if the provided data dict is in the
        correct format. Not if the field id actually exists.

        Example format:
        {
            FIELD_ID: {
                "value": 200
            }
        }

        :param data: The data that needs to be validated.
        :type data: dict
        :return: The validated dict.
        :rtype: dict
        """

        internal = {}
        for key, value in data.items():
            if not (isinstance(key, int) or (isinstance(key, str) and key.isnumeric())):
                self.fail("invalid_key")
            serializer = self.serializer_class(data=value)
            if not serializer.is_valid():
                self.fail("invalid_value")
            internal[int(key)] = serializer.data
        return internal

    def to_representation(self, value):
        """
        If the provided value is a GridView instance we need to fetch the options from
        the database. We can easily use the `get_field_options` of the GridView for
        that and format the dict the way we want.

        If the provided value is a dict it means the field options have already been
        provided and validated once, so we can just return that value. The variant is
        used when we want to validate the input.

        :param value: The prepared value that needs to be serialized.
        :type value: GridView or dict
        :return: A dictionary containing the
        :rtype: dict
        """

        if isinstance(value, View):
            # If the fields are in the context we can pass them into the
            # `get_field_options` call so that they don't have to be fetched from the
            # database again.
            fields = self.context.get("fields")
            return {
                field_options.field_id: self.serializer_class(field_options).data
                for field_options in value.get_field_options(True, fields)
            }
        else:
            return value


class ViewFilterSerializer(serializers.ModelSerializer):
    preload_values = serializers.DictField(
        help_text="Can contain unique preloaded values per filter. This is for "
        "example used by the `link_row_has` filter to communicate the display name if "
        "a value is provided.",
        read_only=True,
    )

    class Meta:
        model = ViewFilter
        fields = ("id", "view", "field", "type", "value", "preload_values")
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
    type = serializers.ChoiceField(
        choices=lazy(view_type_registry.get_types, list)(), required=True
    )

    class Meta:
        model = View
        fields = ("name", "type", "filter_type", "filters_disabled")


class UpdateViewSerializer(serializers.ModelSerializer):
    class Meta:
        ref_name = "view update"
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

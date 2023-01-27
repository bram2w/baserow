from django.utils.functional import lazy

from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.api.fields.serializers import FieldSerializer
from baserow.contrib.database.api.serializers import TableSerializer
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.views.models import (
    OWNERSHIP_TYPE_COLLABORATIVE,
    View,
    ViewDecoration,
    ViewFilter,
    ViewSort,
)
from baserow.contrib.database.views.registries import (
    decorator_type_registry,
    decorator_value_provider_type_registry,
    view_filter_type_registry,
    view_ownership_type_registry,
    view_type_registry,
)


class ListQueryParamatersSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, default=None)
    type = serializers.ChoiceField(
        required=False,
        default=None,
        choices=lazy(view_type_registry.get_types, list)(),
    )


class FieldOptionsField(serializers.Field):
    default_error_messages = {
        "invalid_key": "Field option key must be numeric.",
        "invalid_value": "Must be valid field options.",
    }

    def __init__(self, serializer_class, create_if_missing=True, **kwargs):
        self.serializer_class = serializer_class
        self.create_if_missing = create_if_missing
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
            field_options = self.context.get("field_options", None)
            if field_options is None:
                # If the fields are in the context we can pass them into the
                # `get_field_options` call so that they don't have to be fetched from
                # the database again.
                field_options = value.get_field_options(
                    self.create_if_missing, self.context.get("fields")
                )
            return {
                field_options.field_id: self.serializer_class(field_options).data
                for field_options in field_options
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


class ViewDecorationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewDecoration
        fields = (
            "id",
            "view",
            "type",
            "value_provider_type",
            "value_provider_conf",
            "order",
        )
        extra_kwargs = {
            "id": {"read_only": True, "required": False},
            "view": {"required": False},
            "type": {"required": False},
            "value_provider_conf": {"required": False},
        }


def _only_empty_dict(value):
    if not (isinstance(value, dict) and not value):
        raise serializers.ValidationError("This field should be an empty object.")


class UpdateViewDecorationSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=lazy(decorator_type_registry.get_types, list)(),
        required=False,
        help_text=ViewDecoration._meta.get_field("type").help_text,
    )
    value_provider_type = serializers.ChoiceField(
        choices=lazy(
            lambda: [""] + decorator_value_provider_type_registry.get_types(),
            list,
        )(),
        required=False,
        help_text=ViewDecoration._meta.get_field("value_provider_type").help_text,
    )
    value_provider_conf = serializers.DictField(
        required=False,
        validators=[_only_empty_dict],
        help_text=ViewDecoration._meta.get_field("value_provider_conf").help_text,
    )

    class Meta:
        model = ViewDecoration
        fields = ("type", "value_provider_type", "value_provider_conf", "order")
        extra_kwargs = {
            "order": {"required": False},
        }


class CreateViewDecorationSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=lazy(decorator_type_registry.get_types, list)(),
        required=True,
        help_text=ViewDecoration._meta.get_field("type").help_text,
    )
    value_provider_type = serializers.ChoiceField(
        choices=lazy(
            lambda: [""] + decorator_value_provider_type_registry.get_types(),
            list,
        )(),
        default="",
        required=False,
        help_text=ViewDecoration._meta.get_field("value_provider_type").help_text,
    )
    value_provider_conf = serializers.DictField(
        required=False,
        default=dict,
        validators=[_only_empty_dict],
        help_text=ViewDecoration._meta.get_field("value_provider_conf").help_text,
    )

    class Meta:
        model = ViewDecoration
        fields = ("type", "value_provider_type", "value_provider_conf", "order")
        extra_kwargs = {
            "order": {"required": False},
        }


class ViewSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    table = TableSerializer()
    filters = ViewFilterSerializer(many=True, source="viewfilter_set", required=False)
    sortings = ViewSortSerializer(many=True, source="viewsort_set", required=False)
    decorations = ViewDecorationSerializer(
        many=True, source="viewdecoration_set", required=False
    )
    show_logo = serializers.BooleanField(required=False)
    ownership_type = serializers.CharField()

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
            "decorations",
            "filters_disabled",
            "public_view_has_password",
            "show_logo",
            "ownership_type",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "table_id": {"read_only": True},
            "public_view_has_password": {"read_only": True},
            "ownership_type": {"read_only": True},
        }

    def __init__(self, *args, **kwargs):
        context = kwargs.setdefault("context", {})
        context["include_filters"] = kwargs.pop("filters", False)
        context["include_sortings"] = kwargs.pop("sortings", False)
        context["include_decorations"] = kwargs.pop("decorations", False)
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        # We remove the fields in to_representation rather than __init__ as otherwise
        # drf-spectacular will not know that filters, sortings and decorations exist as
        # optional return fields.
        # This way the fields are still dynamic and also show up in the OpenAPI
        # specification.
        if not self.context["include_filters"]:
            self.fields.pop("filters", None)

        if not self.context["include_sortings"]:
            self.fields.pop("sortings", None)

        if not self.context["include_decorations"]:
            self.fields.pop("decorations", None)

        return super().to_representation(instance)

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        return view_type_registry.get_by_model(instance.specific_class).type


class CreateViewSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=lazy(view_type_registry.get_types, list)(), required=True
    )
    ownership_type = serializers.ChoiceField(
        choices=lazy(view_ownership_type_registry.get_types, list)(),
        default=OWNERSHIP_TYPE_COLLABORATIVE,
    )

    class Meta:
        model = View
        fields = ("name", "type", "ownership_type", "filter_type", "filters_disabled")


class UpdateViewSerializer(serializers.ModelSerializer):
    def _make_password(self, plain_password: str):
        """
        An empty string disables password protection.
        A non-empty string will be encrypted and used to check user authorization.

        :param plain_password: The password to encrypt.
        :return: The encrypted password or "" if disabled.
        """

        return View.make_password(plain_password) if plain_password else ""

    def to_internal_value(self, data):
        plain_password = data.get("public_view_password")
        if plain_password is not None:
            data = {
                **data,
                "public_view_password": self._make_password(plain_password),
            }

        return super().to_internal_value(data)

    class Meta:
        ref_name = "view_update"
        model = View
        fields = ("name", "filter_type", "filters_disabled", "public_view_password")
        extra_kwargs = {
            "name": {"required": False},
            "filter_type": {"required": False},
            "filters_disabled": {"required": False},
        }


class OrderViewsSerializer(serializers.Serializer):
    view_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="View ids in the desired order.",
        min_length=1,
    )


class PublicViewAuthRequestSerializer(serializers.Serializer):
    password = serializers.CharField()


class PublicViewAuthResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()


class PublicViewSortSerializer(serializers.ModelSerializer):
    view = serializers.SlugField(source="view.slug")

    class Meta:
        model = ViewSort
        fields = ("id", "view", "field", "order")
        extra_kwargs = {"id": {"read_only": True}}


class PublicViewTableSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    database_id = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.INT)
    def get_id(self, instance):
        return PUBLIC_PLACEHOLDER_ENTITY_ID

    @extend_schema_field(OpenApiTypes.INT)
    def get_database_id(self, instance):
        return PUBLIC_PLACEHOLDER_ENTITY_ID


class PublicViewSerializer(serializers.ModelSerializer):
    id = serializers.SlugField(source="slug")
    table = PublicViewTableSerializer()
    type = serializers.SerializerMethodField()
    sortings = serializers.SerializerMethodField()
    show_logo = serializers.BooleanField(required=False)

    @extend_schema_field(PublicViewSortSerializer(many=True))
    def get_sortings(self, instance):
        sortings = PublicViewSortSerializer(
            instance=instance.viewsort_set.filter(field__in=self.context["fields"]),
            many=True,
        )
        return sortings.data

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        return view_type_registry.get_by_model(instance.specific_class).type

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
            "show_logo",
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


class PublicViewInfoSerializer(serializers.Serializer):
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
    @extend_schema_field(PublicViewSerializer)
    def get_view(self, instance):
        return view_type_registry.get_serializer(
            instance, PublicViewSerializer, context=self.context
        ).data

    def __init__(self, *args, **kwargs):
        kwargs["context"] = kwargs.get("context", {})
        kwargs["context"]["fields"] = kwargs.pop("fields", [])
        super().__init__(instance=kwargs.pop("view", None), *args, **kwargs)


class FieldWithFiltersAndSortsSerializer(FieldSerializer):
    filters = ViewFilterSerializer(many=True, source="viewfilter_set")
    sortings = ViewSortSerializer(many=True, source="viewsort_set")

    class Meta(FieldSerializer.Meta):
        fields = FieldSerializer.Meta.fields + (
            "filters",
            "sortings",
        )

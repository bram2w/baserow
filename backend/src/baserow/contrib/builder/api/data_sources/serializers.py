from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.api.services.serializers import (
    CreateServiceSerializer,
    ServiceSerializer,
    UpdateServiceSerializer,
)
from baserow.contrib.builder.data_sources.models import DataSource
from baserow.core.services.registries import service_type_registry


class DataSourceSerializer(ServiceSerializer):
    """
    Basic data_source serializer mostly for returned values. This serializer flatten the
    service properties so that from an API POV the data_source object only exists.
    """

    id = serializers.SerializerMethodField(help_text="Data source id.")
    name = serializers.SerializerMethodField(
        help_text=DataSource._meta.get_field("name").help_text
    )
    page_id = serializers.SerializerMethodField(
        help_text=DataSource._meta.get_field("page").help_text
    )
    order = serializers.SerializerMethodField(
        help_text=DataSource._meta.get_field("order").help_text
    )
    type = serializers.SerializerMethodField(help_text="The type of the data source.")

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        if isinstance(instance, DataSource):
            return None
        else:
            return service_type_registry.get_by_model(instance.specific_class).type

    @extend_schema_field(OpenApiTypes.INT)
    def get_id(self, instance):
        return self.context["data_source"].id

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, instance):
        return self.context["data_source"].name

    @extend_schema_field(OpenApiTypes.INT)
    def get_page_id(self, instance):
        return self.context["data_source"].page_id

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_order(self, instance):
        return self.context["data_source"].order

    class Meta(ServiceSerializer.Meta):
        fields = ServiceSerializer.Meta.fields + ("name", "page_id", "order")
        extra_kwargs = {
            **ServiceSerializer.Meta.extra_kwargs,
            "name": {"read_only": True},
            "page_id": {"read_only": True},
            "order": {"read_only": True, "help_text": "Lowest first."},
        }


class CreateDataSourceSerializer(CreateServiceSerializer):
    """
    This serializer allow to set the type of a data_source and the data_source id
    before which we want to insert the new data_source.
    """

    name = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=DataSource._meta.get_field("name").help_text,
    )
    page_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text=DataSource._meta.get_field("page").help_text,
    )
    before_id = serializers.IntegerField(
        required=False,
        help_text="If provided, creates the data_source before the data_source with the "
        "given id.",
    )
    type = serializers.ChoiceField(
        choices=lazy(service_type_registry.get_types, list)(),
        required=False,
        help_text="The type of the service.",
    )

    class Meta(ServiceSerializer.Meta):
        fields = CreateServiceSerializer.Meta.fields + (
            "name",
            "page_id",
            "before_id",
        )


class BaseUpdateDataSourceSerializer(serializers.ModelSerializer):
    class Meta(ServiceSerializer.Meta):
        model = DataSource
        fields = ("name",)
        extra_kwargs = {
            "name": {"required": False},
        }


class UpdateDataSourceSerializer(UpdateServiceSerializer):
    name = serializers.CharField(required=False)

    class Meta(ServiceSerializer.Meta):
        fields = UpdateServiceSerializer.Meta.fields + ("name",)


class MoveDataSourceSerializer(serializers.Serializer):
    before_id = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text=(
            "If provided, the data_source is moved before the data_source with this Id. "
            "Otherwise the data_source is placed  last for this page."
        ),
    )

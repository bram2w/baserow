from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.api.applications.serializers import ApplicationSerializer
from baserow.contrib.database.api.tables.serializers import TableSerializer
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.views.models import View


class LocalBaserowViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = View
        fields = ("id", "table_id", "name")


class LocalBaserowFieldSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField(help_text="The type of the related field.")

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        return field_type_registry.get_by_model(instance.specific_class).type

    class Meta:
        model = Field
        fields = ("id", "table_id", "name", "type")


class TableSerializerWithFields(TableSerializer):
    fields = LocalBaserowFieldSerializer(many=True, help_text="Fields of this table")

    class Meta(TableSerializer.Meta):
        fields = ("id", "name", "order", "database_id", "fields")


class LocalBaserowDatabaseSerializer(ApplicationSerializer):
    tables = TableSerializerWithFields(
        many=True,
        help_text="This field is specific to the `database` application and contains "
        "an array of tables that are in the database.",
    )
    views = LocalBaserowViewSerializer(
        many=True,
        help_text="This field is specific to the `database` application and contains "
        "an array of views that are in the tables.",
    )

    class Meta(ApplicationSerializer.Meta):
        ref_name = "DatabaseApplication"
        fields = ApplicationSerializer.Meta.fields + ("tables", "views")


class LocalBaserowContextDataSerializer(serializers.Serializer):
    databases = LocalBaserowDatabaseSerializer(many=True)

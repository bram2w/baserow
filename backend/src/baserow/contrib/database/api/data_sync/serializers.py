from django.utils.functional import lazy

from rest_framework import serializers

from baserow.contrib.database.data_sync.models import DataSync, DataSyncSyncedProperty
from baserow.contrib.database.data_sync.registries import data_sync_type_registry
from baserow.contrib.database.fields.registries import field_type_registry


class DataSyncSyncedPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSyncSyncedProperty
        fields = ("field_id", "key", "unique_primary")


class DataSyncSerializer(serializers.ModelSerializer):
    synced_properties = DataSyncSyncedPropertySerializer(many=True)

    class Meta:
        model = DataSync
        fields = (
            "id",
            "synced_properties",
            "last_sync",
            "last_error",
        )


class CreateDataSyncSerializer(serializers.ModelSerializer):
    synced_properties = serializers.ListField(
        child=serializers.CharField(), required=True
    )
    type = serializers.ChoiceField(
        choices=lazy(data_sync_type_registry.get_types, list)(),
        help_text="The type of the data sync table that must be created.",
        required=True,
    )
    table_name = serializers.CharField(required=True)

    class Meta:
        model = DataSync
        fields = ("synced_properties", "type", "table_name")


class ListDataSyncPropertiesRequestSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=lazy(data_sync_type_registry.get_types, list)(),
        help_text="The type of the data sync to get the properties from.",
        required=True,
    )

    class Meta:
        model = DataSync
        fields = ("type",)


class ListDataSyncPropertySerializer(serializers.Serializer):
    unique_primary = serializers.BooleanField()
    key = serializers.CharField()
    name = serializers.CharField()
    field_type = serializers.SerializerMethodField()

    def get_field_type(self, instance):
        field_type = field_type_registry.get_by_model(instance.to_baserow_field())
        return field_type.type

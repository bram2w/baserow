from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from baserow.api.applications.serializers import ApplicationSerializer
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.api.tables.serializers import TableSerializer


class DatabaseSerializer(ApplicationSerializer):
    tables = serializers.SerializerMethodField(
        help_text="This field is specific to the `database` application and contains "
        "an array of tables that are in the database."
    )

    class Meta(ApplicationSerializer.Meta):
        ref_name = "DatabaseApplication"
        fields = ApplicationSerializer.Meta.fields + ("tables",)

    @extend_schema_field(TableSerializer(many=True))
    def get_tables(self, instance):
        """
        Because the the instance doesn't know at this point it is a Database we have to
        select the related tables this way.

        :param instance: The database application instance.
        :type instance: Application
        :return: A list of serialized tables that belong to this instance.
        :rtype: list
        """

        tables = Table.objects.filter(database_id=instance.pk)
        return TableSerializer(tables, many=True).data

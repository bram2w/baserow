from typing import List

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.api.applications.serializers import ApplicationSerializer
from baserow.contrib.database.api.tables.serializers import TableSerializer
from baserow.contrib.database.operations import ListTablesDatabaseTableOperationType
from baserow.contrib.database.table.models import Table
from baserow.core.handler import CoreHandler
from baserow.core.models import Application


class DatabaseSerializer(ApplicationSerializer):
    tables = serializers.SerializerMethodField(
        help_text="This field is specific to the `database` application and contains "
        "an array of tables that are in the database."
    )

    class Meta(ApplicationSerializer.Meta):
        ref_name = "DatabaseApplication"
        fields = ApplicationSerializer.Meta.fields + ("tables",)

    @extend_schema_field(TableSerializer(many=True))
    def get_tables(self, instance: Application) -> List:
        """
        Because the instance doesn't know at this point it is a Database we have to
        select the related tables this way.

        :param instance: The database application instance.
        :return: A list of serialized tables that belong to this instance.
        """

        tables = Table.objects.filter(database_id=instance.pk)

        user = self.context.get("user")
        request = self.context.get("request")

        if user is None and hasattr(request, "user"):
            user = request.user

        if user:
            tables = CoreHandler().filter_queryset(
                user,
                ListTablesDatabaseTableOperationType.type,
                tables,
                group=instance.group,
                context=instance,
                allow_if_template=True,
            )

        return TableSerializer(tables, many=True).data

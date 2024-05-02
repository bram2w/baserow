from typing import List

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.contrib.database.api.tables.serializers import TableSerializer
from baserow.contrib.database.models import Database
from baserow.contrib.database.operations import ListTablesDatabaseTableOperationType
from baserow.core.handler import CoreHandler


class DatabaseSerializer(serializers.ModelSerializer):
    tables = serializers.SerializerMethodField(
        help_text="This field is specific to the `database` application and contains "
        "an array of tables that are in the database."
    )

    class Meta:
        model = Database
        fields = (
            "id",
            "name",
            "tables",
        )

    @extend_schema_field(TableSerializer(many=True))
    def get_tables(self, instance: Database) -> List:
        """
        Because the instance doesn't know at this point it is a Database we have to
        select the related tables this way.

        :param instance: The database application instance.
        :return: A list of serialized tables that belong to this instance.
        """

        tables = instance.table_set.all()
        user = self.context.get("user")
        request = self.context.get("request")

        if user is None and hasattr(request, "user"):
            user = request.user

        if user:
            tables = CoreHandler().filter_queryset(
                user,
                ListTablesDatabaseTableOperationType.type,
                tables,
                workspace=instance.workspace,
            )

        return TableSerializer(tables, many=True).data

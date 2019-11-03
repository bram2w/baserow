from rest_framework import serializers

from baserow.api.v0.applications.serializers import ApplicationSerializer
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.api.v0.tables.serializers import TableSerializer


class DatabaseSerializer(ApplicationSerializer):
    tables = serializers.SerializerMethodField()

    class Meta(ApplicationSerializer.Meta):
        fields = ApplicationSerializer.Meta.fields + ('tables',)

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

from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from baserow.api.v0.decorators import validate_body, map_exceptions
from baserow.api.v0.errors import ERROR_USER_NOT_IN_GROUP
from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.models import Database
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.table.handler import TableHandler

from .serializers import TableSerializer, TableCreateUpdateSerializer


class TablesView(APIView):
    permission_classes = (IsAuthenticated,)
    table_handler = TableHandler()

    @staticmethod
    def get_database(user, database_id):
        database = get_object_or_404(
            Database.objects.select_related('group'),
            pk=database_id
        )

        if not database.group.has_user(user):
            raise UserNotInGroupError(user, database.group)

        return database

    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, database_id):
        """Lists all the tables of a database."""

        database = self.get_database(request.user, database_id)
        tables = Table.objects.filter(database=database)
        serializer = TableSerializer(tables, many=True)
        return Response(serializer.data)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    @validate_body(TableCreateUpdateSerializer)
    def post(self, request, data, database_id):
        """Creates a new table in a database."""

        database = self.get_database(request.user, database_id)
        table = self.table_handler.create_table(
            request.user, database, name=data['name'])
        serializer = TableSerializer(table)
        return Response(serializer.data)


class TableView(APIView):
    permission_classes = (IsAuthenticated,)
    table_handler = TableHandler()

    @staticmethod
    def get_table(user, table_id):
        table = get_object_or_404(
            Table.objects.select_related('database__group'),
            pk=table_id
        )

        if not table.database.group.has_user(user):
            raise UserNotInGroupError(user, table.database.group)

        return table

    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, table_id):
        """Responds with a serialized table instance."""

        table = self.get_table(request.user, table_id)
        serializer = TableSerializer(table)
        return Response(serializer.data)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    @validate_body(TableCreateUpdateSerializer)
    def patch(self, request, data, table_id):
        """Updates the values a table instance."""

        table = self.table_handler.update_table(
            request.user,
            self.get_table(request.user, table_id),
            name=data['name']
        )
        serializer = TableSerializer(table)
        return Response(serializer.data)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def delete(self, request, table_id):
        """Deletes an existing table."""

        self.table_handler.delete_table(
            request.user,
            self.get_table(request.user, table_id)
        )
        return Response(status=204)

from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes

from baserow.api.decorators import validate_body, map_exceptions
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.models import Database
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.table.handler import TableHandler

from .serializers import TableSerializer, TableCreateUpdateSerializer


class TablesView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get_database(user, database_id):
        database = get_object_or_404(
            Database.objects.select_related('group'),
            pk=database_id
        )

        if not database.group.has_user(user):
            raise UserNotInGroupError(user, database.group)

        return database

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='database_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Returns only tables that are related to the provided '
                            'value.'
            )
        ],
        tags=['Database tables'],
        operation_id='list_database_tables',
        description=(
            'Lists all the tables that are in the database related to the '
            '`database_id` parameter if the user has access to the database\'s group. '
            'A table is exactly as the name suggests. It can hold multiple fields, '
            'each having their own type and multiple rows. They can be added via the '
            '**create_database_table_field** and **create_database_table_row** '
            'endpoints.'
        ),
        responses={
            200: TableSerializer(many=True),
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP'])
        }
    )
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, database_id):
        """Lists all the tables of a database."""

        database = self.get_database(request.user, database_id)
        tables = Table.objects.filter(database=database)
        serializer = TableSerializer(tables, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='database_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Creates a table for the database related to the provided '
                            'value.'
            )
        ],
        tags=['Database tables'],
        operation_id='create_database_table',
        description=(
            'Creates a new table for the database related to the provided '
            '`database_id` parameter if the authorized user has access to the '
            'database\'s group.'
        ),
        request=TableCreateUpdateSerializer,
        responses={
            200: TableSerializer,
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP', 'ERROR_REQUEST_BODY_VALIDATION'
            ])
        }
    )
    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    @validate_body(TableCreateUpdateSerializer)
    def post(self, request, data, database_id):
        """Creates a new table in a database."""

        database = self.get_database(request.user, database_id)
        table = TableHandler().create_table(
            request.user, database, fill_initial=True, name=data['name'])
        serializer = TableSerializer(table)
        return Response(serializer.data)


class TableView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get_table(user, table_id):
        table = get_object_or_404(
            Table.objects.select_related('database__group'),
            pk=table_id
        )

        if not table.database.group.has_user(user):
            raise UserNotInGroupError(user, table.database.group)

        return table

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='table_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Returns the table related to the provided value.'
            )
        ],
        tags=['Database tables'],
        operation_id='get_database_table',
        description=(
            'Returns the requested table if the authorized user has access to the '
            'related database\'s group.'
        ),
        responses={
            200: TableSerializer,
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP'])
        }
    )
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, table_id):
        """Responds with a serialized table instance."""

        table = self.get_table(request.user, table_id)
        serializer = TableSerializer(table)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='table_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Updates the table related to the provided value.'
            )
        ],
        tags=['Database tables'],
        operation_id='update_database_table',
        description=(
            'Updates the existing table if the authorized user has access to the '
            'related database\'s group.'
        ),
        request=TableCreateUpdateSerializer,
        responses={
            200: TableSerializer,
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP', 'ERROR_REQUEST_BODY_VALIDATION'
            ])
        }
    )
    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    @validate_body(TableCreateUpdateSerializer)
    def patch(self, request, data, table_id):
        """Updates the values a table instance."""

        table = TableHandler().update_table(
            request.user,
            self.get_table(request.user, table_id),
            name=data['name']
        )
        serializer = TableSerializer(table)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='table_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Deletes the table related to the provided value.'
            )
        ],
        tags=['Database tables'],
        operation_id='delete_database_table',
        description=(
            'Deletes the existing table if the authorized user has access to the '
            'related database\'s group.'
        ),
        responses={
            204: None,
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP'])
        }
    )
    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def delete(self, request, table_id):
        """Deletes an existing table."""

        TableHandler().delete_table(
            request.user,
            self.get_table(request.user, table_id)
        )
        return Response(status=204)

from django.db import transaction
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes

from baserow.api.utils import validate_data
from baserow.api.decorators import map_exceptions
from baserow.api.pagination import PageNumberPagination
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.api.user_files.errors import ERROR_USER_FILE_DOES_NOT_EXIST
from baserow.core.exceptions import UserNotInGroupError
from baserow.core.user_files.exceptions import UserFileDoesNotExist
from baserow.contrib.database.api.tokens.authentications import TokenAuthentication
from baserow.contrib.database.api.tables.errors import ERROR_TABLE_DOES_NOT_EXIST
from baserow.contrib.database.api.rows.errors import ERROR_ROW_DOES_NOT_EXIST
from baserow.contrib.database.api.rows.serializers import (
    example_pagination_row_serializer_class
)
from baserow.contrib.database.api.tokens.errors import ERROR_NO_PERMISSION_TO_TABLE
from baserow.contrib.database.api.fields.errors import (
    ERROR_ORDER_BY_FIELD_NOT_POSSIBLE, ERROR_ORDER_BY_FIELD_NOT_FOUND
)
from baserow.contrib.database.fields.exceptions import (
    OrderByFieldNotFound, OrderByFieldNotPossible
)
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.rows.exceptions import RowDoesNotExist
from baserow.contrib.database.tokens.handler import TokenHandler
from baserow.contrib.database.tokens.exceptions import NoPermissionToTable

from .serializers import (
    RowSerializer, get_example_row_serializer_class, get_row_serializer_class
)


class RowsView(APIView):
    authentication_classes = APIView.authentication_classes + [TokenAuthentication]
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='table_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Returns the rows of the table related to the provided '
                            'value.'
            ),
            OpenApiParameter(
                name='page',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description='Defines which page of rows should be returned.'
            ),
            OpenApiParameter(
                name='size',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description='Defines how many rows should be returned per page.'
            ),
            OpenApiParameter(
                name='search',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description='If provided only rows with data that matches the search '
                            'query are going to be returned.'
            ),
            OpenApiParameter(
                name='order_by',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description='Optionally the rows can be ordered by provided field ids '
                            'separated by comma. By default a field is ordered in '
                            'ascending (A-Z) order, but by prepending the field with '
                            'a \'-\' it can be ordered descending (Z-A). '
            )
        ],
        tags=['Database table rows'],
        operation_id='list_database_table_rows',
        description=(
            'Lists all the rows of the table related to the provided parameter if the '
            'user has access to the related database\'s group. The response is '
            'paginated by a page/size style. It is also possible to provide an '
            'optional search query, only rows where the data matches the search query '
            'are going to be returned then. The properties of the returned rows '
            'depends on which fields the table has. For a complete overview of fields '
            'use the **list_database_table_fields** endpoint to list them all. In the '
            'example all field types are listed, but normally the number in '
            'field_{id} key is going to be the id of the field. The value is what the '
            'user has provided and the format of it depends on the fields type.'
        ),
        responses={
            200: example_pagination_row_serializer_class,
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP',
                'ERROR_REQUEST_BODY_VALIDATION',
                'ERROR_PAGE_SIZE_LIMIT',
                'ERROR_INVALID_PAGE',
                'ERROR_ORDER_BY_FIELD_NOT_FOUND',
                'ERROR_ORDER_BY_FIELD_NOT_POSSIBLE'
            ]),
            401: get_error_schema(['ERROR_NO_PERMISSION_TO_TABLE']),
            404: get_error_schema(['ERROR_TABLE_DOES_NOT_EXIST'])
        }
    )
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
        NoPermissionToTable: ERROR_NO_PERMISSION_TO_TABLE,
        OrderByFieldNotFound: ERROR_ORDER_BY_FIELD_NOT_FOUND,
        OrderByFieldNotPossible: ERROR_ORDER_BY_FIELD_NOT_POSSIBLE
    })
    def get(self, request, table_id):
        """
        Lists all the rows of the given table id paginated. It is also possible to
        provide a search query.
        """

        table = TableHandler().get_table(request.user, table_id)
        TokenHandler().check_table_permissions(request, 'read', table, False)

        model = table.get_model()
        search = request.GET.get('search')
        order_by = request.GET.get('order_by')

        queryset = model.objects.all().enhance_by_fields().order_by('id')

        if search:
            queryset = queryset.search_all_fields(search)

        if order_by:
            queryset = queryset.order_by_fields_string(order_by)

        paginator = PageNumberPagination(limit_page_size=settings.ROW_PAGE_SIZE_LIMIT)
        page = paginator.paginate_queryset(queryset, request, self)
        serializer_class = get_row_serializer_class(model, RowSerializer,
                                                    is_response=True)
        serializer = serializer_class(page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='table_id', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                description='Creates a row in the table related to the provided '
                            'value.'
            )
        ],
        tags=['Database table rows'],
        operation_id='create_database_table_row',
        description=(
            'Creates a new row in the table if the user has access to the related '
            'table\'s group. The accepted body fields are depending on the fields '
            'that the table has. For a complete overview of fields use the '
            '**list_database_table_fields** to list them all. None of the fields are '
            'required, if they are not provided the value is going to be `null` or '
            '`false` or some default value is that is set. If you want to add a value '
            'for the field with for example id `10`, the key must be named '
            '`field_10`. Of course multiple fields can be provided in one request. In '
            'the examples below you will find all the different field types, the '
            'numbers/ids in the example are just there for example purposes, the '
            'field_ID must be replaced with the actual id of the field.'
        ),
        request=get_example_row_serializer_class(False),
        responses={
            200: get_example_row_serializer_class(True),
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP',
                'ERROR_REQUEST_BODY_VALIDATION'
            ]),
            401: get_error_schema(['ERROR_NO_PERMISSION_TO_TABLE']),
            404: get_error_schema([
                'ERROR_TABLE_DOES_NOT_EXIST'
            ])
        }
    )
    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
        NoPermissionToTable: ERROR_NO_PERMISSION_TO_TABLE,
        UserFileDoesNotExist: ERROR_USER_FILE_DOES_NOT_EXIST
    })
    def post(self, request, table_id):
        """
        Creates a new row for the given table_id. Also the post data is validated
        according to the tables field types.
        """

        table = TableHandler().get_table(request.user, table_id)
        TokenHandler().check_table_permissions(request, 'create', table, False)
        model = table.get_model()

        validation_serializer = get_row_serializer_class(model)
        data = validate_data(validation_serializer, request.data)

        row = RowHandler().create_row(request.user, table, data, model)
        serializer_class = get_row_serializer_class(model, RowSerializer,
                                                    is_response=True)
        serializer = serializer_class(row)

        return Response(serializer.data)


class RowView(APIView):
    authentication_classes = APIView.authentication_classes + [TokenAuthentication]
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='table_id', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                description='Returns the row of the table related to the provided '
                            'value.'
            ),
            OpenApiParameter(
                name='row_id', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                description='Returns the row related the provided value.'
            )
        ],
        tags=['Database table rows'],
        operation_id='get_database_table_row',
        description=(
            'Fetches an existing row from the table if the user has access to the '
            'related table\'s group. The properties of the returned row depend on '
            'which fields the table has. For a complete overview of fields use the '
            '**list_database_table_fields** endpoint to list them all. In the example '
            'all field types are listed, but normally the number in field_{id} key is '
            'going to be the id of the field. The value is what the user has provided '
            'and the format of it depends on the fields type.'
        ),
        responses={
            200: get_example_row_serializer_class(True),
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP',
                'ERROR_REQUEST_BODY_VALIDATION'
            ]),
            401: get_error_schema(['ERROR_NO_PERMISSION_TO_TABLE']),
            404: get_error_schema([
                'ERROR_TABLE_DOES_NOT_EXIST',
                'ERROR_ROW_DOES_NOT_EXIST'
            ])
        }
    )
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
        RowDoesNotExist: ERROR_ROW_DOES_NOT_EXIST,
        NoPermissionToTable: ERROR_NO_PERMISSION_TO_TABLE
    })
    def get(self, request, table_id, row_id):
        """
        Responds with a serializer version of the row related to the provided row_id
        and table_id.
        """

        table = TableHandler().get_table(request.user, table_id)
        TokenHandler().check_table_permissions(request, 'read', table, False)

        model = table.get_model()
        row = RowHandler().get_row(request.user, table, row_id, model)
        serializer_class = get_row_serializer_class(model, RowSerializer,
                                                    is_response=True)
        serializer = serializer_class(row)

        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='table_id', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                description='Updates the row in the table related to the value.'
            ),
            OpenApiParameter(
                name='row_id', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                description='Updates the row related to the value.'
            )
        ],
        tags=['Database table rows'],
        operation_id='update_database_table_row',
        description=(
            'Updates an existing row in the table if the user has access to the '
            'related table\'s group. The accepted body fields are depending on the '
            'fields that the table has. For a complete overview of fields use the '
            '**list_database_table_fields** endpoint to list them all. None of the '
            'fields are required, if they are not provided the value is not going to '
            'be updated. If you want to update a value for the field with for example '
            'id `10`, the key must be named `field_10`. Of course multiple fields can '
            'be provided in one request. In the examples below you will find all the '
            'different field types, the numbers/ids in the example are just there for '
            'example purposes, the field_ID must be replaced with the actual id of the '
            'field.'
        ),
        request=get_example_row_serializer_class(False),
        responses={
            200: get_example_row_serializer_class(True),
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP',
                'ERROR_REQUEST_BODY_VALIDATION'
            ]),
            401: get_error_schema(['ERROR_NO_PERMISSION_TO_TABLE']),
            404: get_error_schema([
                'ERROR_TABLE_DOES_NOT_EXIST',
                'ERROR_ROW_DOES_NOT_EXIST'
            ])
        }
    )
    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
        RowDoesNotExist: ERROR_ROW_DOES_NOT_EXIST,
        NoPermissionToTable: ERROR_NO_PERMISSION_TO_TABLE,
        UserFileDoesNotExist: ERROR_USER_FILE_DOES_NOT_EXIST
    })
    def patch(self, request, table_id, row_id):
        """
        Updates the row with the given row_id for the table with the given
        table_id. Also the post data is validated according to the tables field types.
        """

        table = TableHandler().get_table(request.user, table_id)
        TokenHandler().check_table_permissions(request, 'update', table, False)

        # Small side effect of generating the model for only the fields that need to
        # change is that the response it not going to contain the other fields. It is
        # however much faster because it doesn't need to get the specific version of
        # all the field objects.
        field_ids = RowHandler().extract_field_ids_from_dict(request.data)
        model = table.get_model(field_ids=field_ids)

        validation_serializer = get_row_serializer_class(model)
        data = validate_data(validation_serializer, request.data)

        row = RowHandler().update_row(request.user, table, row_id, data, model)

        serializer_class = get_row_serializer_class(model, RowSerializer,
                                                    is_response=True)
        serializer = serializer_class(row)

        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='table_id', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                description='Deletes the row in the table related to the value.'
            ),
            OpenApiParameter(
                name='row_id', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                description='Deletes the row related to the value.'
            )
        ],
        tags=['Database table rows'],
        operation_id='delete_database_table_row',
        description=(
            'Deletes an existing row in the table if the user has access to the '
            'table\'s group.'
        ),
        responses={
            204: None,
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema([
                'ERROR_TABLE_DOES_NOT_EXIST',
                'ERROR_ROW_DOES_NOT_EXIST'
            ])
        }
    )
    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
        RowDoesNotExist: ERROR_ROW_DOES_NOT_EXIST,
        NoPermissionToTable: ERROR_NO_PERMISSION_TO_TABLE
    })
    def delete(self, request, table_id, row_id):
        """
        Deletes an existing row with the given row_id for table with the given
        table_id.
        """

        table = TableHandler().get_table(request.user, table_id)
        TokenHandler().check_table_permissions(request, 'delete', table, False)
        RowHandler().delete_row(request.user, table, row_id)

        return Response(status=204)

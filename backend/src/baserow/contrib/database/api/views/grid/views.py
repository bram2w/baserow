from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination

from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes

from baserow.api.decorators import map_exceptions, allowed_includes, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.pagination import PageNumberPagination
from baserow.api.schemas import get_error_schema
from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.api.rows.serializers import (
    get_row_serializer_class, RowSerializer
)
from baserow.contrib.database.api.rows.serializers import (
    get_example_row_serializer_class
)
from baserow.contrib.database.api.views.grid.serializers import GridViewSerializer
from baserow.contrib.database.views.exceptions import (
    ViewDoesNotExist, UnrelatedFieldError
)
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import GridView

from .errors import ERROR_GRID_DOES_NOT_EXIST, ERROR_UNRELATED_FIELD
from .serializers import GridViewFilterSerializer


class GridViewView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_id', location=OpenApiParameter.PATH, type=OpenApiTypes.INT,
                description='Returns only rows that belong to the related view\'s '
                            'table.'
            ),
            OpenApiParameter(
                name='include', location=OpenApiParameter.QUERY, type=OpenApiTypes.STR,
                description=(
                    'Can contain `field_options` which will add an object with the '
                    'same name to the response if included. That object contains '
                    'user defined view settings for each field. For example the '
                    'field\'s width is included in here.'
                )
            ),
            OpenApiParameter(
                name='limit', location=OpenApiParameter.QUERY, type=OpenApiTypes.INT,
                description='Defines how many rows should be returned.'
            ),
            OpenApiParameter(
                name='offset', location=OpenApiParameter.QUERY, type=OpenApiTypes.INT,
                description='Can only be used in combination with the `limit` '
                            'parameter and defines from which offset the rows should '
                            'be returned.'
            ),
            OpenApiParameter(
                name='page', location=OpenApiParameter.QUERY, type=OpenApiTypes.INT,
                description='Defines which page of rows should be returned. Either '
                            'the `page` or `limit` can be provided, not both.'
            ),
            OpenApiParameter(
                name='size', location=OpenApiParameter.QUERY, type=OpenApiTypes.INT,
                description='Can only be used in combination with the `page` parameter '
                            'and defines how many rows should be returned.'
            )
        ],
        tags=['Database table grid view'],
        operation_id='list_database_table_grid_view_rows',
        description=(
            'Lists the requested rows of the view\'s table related to the provided '
            '`view_id` if the authorized user has access to the database\'s group. '
            'The response is paginated either by a limit/offset or page/size style. '
            'The style depends on the provided GET parameters. The properties of the '
            'returned rows depends on which fields the table has. For a complete '
            'overview of fields use the **list_database_table_fields** endpoint to '
            'list them all. In the example all field types are listed, but normally '
            'the number in field_{id} key is going to be the id of the field. '
            'The value is what the user has provided and the format of it depends on '
            'the fields type.'
        ),
        responses={
            200: get_example_pagination_serializer_class(
                get_example_row_serializer_class(True)
            ),
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema(['ERROR_GRID_DOES_NOT_EXIST'])
        }
    )
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        ViewDoesNotExist: ERROR_GRID_DOES_NOT_EXIST
    })
    @allowed_includes('field_options')
    def get(self, request, view_id, field_options):
        """
        Lists all the rows of a grid view, paginated either by a page or offset/limit.
        If the limit get parameter is provided the limit/offset pagination will be used
        else the page number pagination.

        Optionally the field options can also be included in the response if the the
        `field_options` are provided in the includes GET parameter.
        """

        view = ViewHandler().get_view(request.user, view_id, GridView)

        model = view.table.get_model()
        queryset = model.objects.all().order_by('id')

        if LimitOffsetPagination.limit_query_param in request.GET:
            paginator = LimitOffsetPagination()
        else:
            paginator = PageNumberPagination()

        page = paginator.paginate_queryset(queryset, request, self)
        serializer_class = get_row_serializer_class(model, RowSerializer)
        serializer = serializer_class(page, many=True)

        response = paginator.get_paginated_response(serializer.data)

        if field_options:
            # The serializer has the GridViewFieldOptionsField which fetches the
            # field options from the database and creates them if they don't exist,
            # but when added to the context the fields don't have to be fetched from
            # the database again when checking if they exist.
            context = {'fields': [o['field'] for o in model._field_objects.values()]}
            response.data.update(**GridViewSerializer(view, context=context).data)

        return response

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                required=False,
                description='Returns only rows that belong to the related view\'s '
                            'table.'
            )
        ],
        tags=['Database table grid view'],
        operation_id='filter_database_table_grid_view_rows',
        description=(
            'Lists only the rows and fields that match the request. Only the rows '
            'with the ids that are in the `row_ids` list are going to be returned. '
            'Same goes for the fields, only the fields with the ids in the '
            '`field_ids` are going to be returned. This endpoint could be used to '
            'refresh data after changes something. For example in the web frontend '
            'after changing a field type, the data of the related cells will be '
            'refreshed using this endpoint. In the example all field types are listed, '
            'but normally  the number in field_{id} key is going to be the id of the '
            'field. The value is what the user has provided and the format of it '
            'depends on the fields type.'
        ),
        request=GridViewFilterSerializer,
        responses={
            200: get_example_row_serializer_class(True)(many=True),
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP', 'ERROR_REQUEST_BODY_VALIDATION'
            ]),
            404: get_error_schema(['ERROR_GRID_DOES_NOT_EXIST'])
        }
    )
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        ViewDoesNotExist: ERROR_GRID_DOES_NOT_EXIST
    })
    @validate_body(GridViewFilterSerializer)
    def post(self, request, view_id, data):
        """
        Row filter endpoint that only lists the requested rows and optionally only the
        requested fields.
        """

        view = ViewHandler().get_view(request.user, view_id, GridView)

        model = view.table.get_model(field_ids=data['field_ids'])
        results = model.objects.filter(pk__in=data['row_ids'])

        serializer_class = get_row_serializer_class(model, RowSerializer)
        serializer = serializer_class(results, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                required=False,
                description='Updates the field related to the provided `view_id` '
                            'parameter.'
            )
        ],
        tags=['Database table grid view'],
        operation_id='update_database_table_grid_view_field_options',
        description=(
            'Updates the field options of a `grid` view. The field options are unique '
            'options per field for a view. This could for example be used to update '
            'the field width if the user changes it.'
        ),
        request=GridViewSerializer,
        responses={
            200: GridViewSerializer,
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP',
                'ERROR_UNRELATED_FIELD',
                'ERROR_REQUEST_BODY_VALIDATION'
            ]),
            404: get_error_schema(['ERROR_GRID_DOES_NOT_EXIST'])
        }
    )
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        ViewDoesNotExist: ERROR_GRID_DOES_NOT_EXIST,
        UnrelatedFieldError: ERROR_UNRELATED_FIELD
    })
    @validate_body(GridViewSerializer)
    def patch(self, request, view_id, data):
        """
        Updates the field options for the provided grid view.

        The following example body data will only update the width of the FIELD_ID
        and leaves the others untouched.
            {
                FIELD_ID: {
                    'width': 200
                }
            }
        """

        handler = ViewHandler()
        view = handler.get_view(request.user, view_id, GridView)
        handler.update_grid_view_field_options(view, data['field_options'])
        return Response(GridViewSerializer(view).data)

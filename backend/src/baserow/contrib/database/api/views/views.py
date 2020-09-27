from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes

from baserow.api.decorators import (
    validate_body, validate_body_custom_fields, map_exceptions, allowed_includes
)
from baserow.api.utils import validate_data_custom_fields
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.utils import PolymorphicCustomFieldRegistrySerializer
from baserow.api.schemas import get_error_schema
from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.api.fields.errors import ERROR_FIELD_NOT_IN_TABLE
from baserow.contrib.database.api.tables.errors import ERROR_TABLE_DOES_NOT_EXIST
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.exceptions import FieldNotInTable
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.views.registries import view_type_registry
from baserow.contrib.database.views.models import View, ViewFilter
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.exceptions import (
    ViewDoesNotExist, ViewFilterDoesNotExist, ViewFilterNotSupported,
    ViewFilterTypeNotAllowedForField
)

from .serializers import (
    ViewSerializer, CreateViewSerializer, UpdateViewSerializer, ViewFilterSerializer,
    CreateViewFilterSerializer, UpdateViewFilterSerializer
)
from .errors import (
    ERROR_VIEW_DOES_NOT_EXIST, ERROR_VIEW_FILTER_DOES_NOT_EXIST,
    ERROR_VIEW_FILTER_NOT_SUPPORTED, ERROR_VIEW_FILTER_TYPE_NOT_ALLOWED_FOR_FIELD
)


class ViewsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='table_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Returns only views of the table related to the provided '
                            'value.'
            )
        ],
        tags=['Database table views'],
        operation_id='list_database_table_views',
        description=(
            'Lists all views of the table related to the provided `table_id` if the '
            'user has access to the related database\'s group. A table can have '
            'multiple views. Each view can display the data in a different way. For '
            'example the `grid` view shows the in a spreadsheet like way. That type '
            'has custom endpoints for data retrieval and manipulation. In the future '
            'other views types like a calendar or Kanban are going to be added. Each '
            'type can have different properties.'
        ),
        responses={
            200: PolymorphicCustomFieldRegistrySerializer(
                view_type_registry,
                ViewSerializer,
                many=True
            ),
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema(['ERROR_TABLE_DOES_NOT_EXIST'])
        }
    )
    @map_exceptions({
        TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    @allowed_includes('filters')
    def get(self, request, table_id, filters):
        """
        Responds with a list of serialized views that belong to the table if the user
        has access to that group.
        """

        table = TableHandler().get_table(request.user, table_id)
        views = View.objects.filter(table=table).select_related('content_type')

        if filters:
            views = views.prefetch_related('viewfilter_set')

        data = [
            view_type_registry.get_serializer(
                view,
                ViewSerializer,
                filters=filters
            ).data
            for view in views
        ]
        return Response(data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='table_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Creates a view for the table related to the provided '
                            'value.'
            )
        ],
        tags=['Database table views'],
        operation_id='create_database_table_view',
        description=(
            'Creates a new view for the table related to the provided `table_id` '
            'parameter if the authorized user has access to the related database\'s '
            'group. Depending on the type, different properties can optionally be '
            'set.'
        ),
        request=PolymorphicCustomFieldRegistrySerializer(
            view_type_registry,
            CreateViewSerializer
        ),
        responses={
            200: PolymorphicCustomFieldRegistrySerializer(
                view_type_registry,
                ViewSerializer
            ),
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP', 'ERROR_REQUEST_BODY_VALIDATION'
            ]),
            404: get_error_schema(['ERROR_TABLE_DOES_NOT_EXIST'])
        }
    )
    @transaction.atomic
    @validate_body_custom_fields(
        view_type_registry, base_serializer_class=CreateViewSerializer)
    @map_exceptions({
        TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    @allowed_includes('filters')
    def post(self, request, data, table_id, filters):
        """Creates a new view for a user."""

        table = TableHandler().get_table(request.user, table_id)
        view = ViewHandler().create_view(
            request.user, table, data.pop('type'), **data)

        serializer = view_type_registry.get_serializer(
            view,
            ViewSerializer,
            filters=filters
        )
        return Response(serializer.data)


class ViewView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Returns the view related to the provided value.'
            )
        ],
        tags=['Database table views'],
        operation_id='get_database_table_view',
        description=(
            'Returns the existing view if the authorized user has access to the '
            'related database\'s group. Depending on the type different properties'
            'could be returned.'
        ),
        responses={
            200: PolymorphicCustomFieldRegistrySerializer(
                view_type_registry,
                ViewSerializer
            ),
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema(['ERROR_VIEW_DOES_NOT_EXIST'])
        }
    )
    @map_exceptions({
        ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    @allowed_includes('filters')
    def get(self, request, view_id, filters):
        """Selects a single view and responds with a serialized version."""

        view = ViewHandler().get_view(request.user, view_id)
        serializer = view_type_registry.get_serializer(
            view,
            ViewSerializer,
            filters=filters
        )
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Updates the view related to the provided value.'
            )
        ],
        tags=['Database table views'],
        operation_id='update_database_table_view',
        description=(
            'Updates the existing view if the authorized user has access to the '
            'related database\'s group. The type cannot be changed. It depends on the '
            'existing type which properties can be changed.'
        ),
        request=PolymorphicCustomFieldRegistrySerializer(
            view_type_registry,
            UpdateViewSerializer
        ),
        responses={
            200: PolymorphicCustomFieldRegistrySerializer(
                view_type_registry,
                ViewSerializer
            ),
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP', 'ERROR_REQUEST_BODY_VALIDATION'
            ]),
            404: get_error_schema(['ERROR_VIEW_DOES_NOT_EXIST'])
        }
    )
    @transaction.atomic
    @map_exceptions({
        ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    @allowed_includes('filters')
    def patch(self, request, view_id, filters):
        """Updates the view if the user belongs to the group."""

        view = ViewHandler().get_view(request.user, view_id).specific
        view_type = view_type_registry.get_by_model(view)
        data = validate_data_custom_fields(
            view_type.type, view_type_registry, request.data,
            base_serializer_class=UpdateViewSerializer
        )

        view = ViewHandler().update_view(request.user, view, **data)

        serializer = view_type_registry.get_serializer(
            view,
            ViewSerializer,
            filters=filters
        )
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Deletes the view related to the provided value.'
            )
        ],
        tags=['Database table views'],
        operation_id='delete_database_table_view',
        description=(
            'Deletes the existing view if the authorized user has access to the '
            'related database\'s group. Note that all the related settings of the '
            'view are going to be deleted also. The data stays intact after deleting '
            'the view because this is related to the table and not the view.'
        ),
        responses={
            204: None,
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema(['ERROR_VIEW_DOES_NOT_EXIST'])
        }
    )
    @transaction.atomic
    @map_exceptions({
        ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def delete(self, request, view_id):
        """Deletes an existing view if the user belongs to the group."""

        view = ViewHandler().get_view(request.user, view_id)
        ViewHandler().delete_view(request.user, view)

        return Response(status=204)


class ViewFiltersView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Returns only filters of the view related to the provided '
                            'value.'
            )
        ],
        tags=['Database table views'],
        operation_id='list_database_table_view_filters',
        description=(
            'Lists all filters of the view related to the provided `view_id` if the '
            'user has access to the related database\'s group. A view can have '
            'multiple filters. When all the rows are requested for the view only those'
            'that apply to the filters are returned.'
        ),
        responses={
            200: ViewFilterSerializer(many=True),
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema(['ERROR_VIEW_DOES_NOT_EXIST'])
        }
    )
    @map_exceptions({
        ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, view_id):
        """
        Responds with a list of serialized filters that belong to the view if the user
        has access to that group.
        """

        view = ViewHandler().get_view(request.user, view_id)
        filters = ViewFilter.objects.filter(view=view)
        serializer = ViewFilterSerializer(filters, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Creates a filter for the view related to the provided '
                            'value.'
            )
        ],
        tags=['Database table views'],
        operation_id='create_database_table_view_filter',
        description=(
            'Creates a new filter for the view related to the provided `view_id` '
            'parameter if the authorized user has access to the related database\'s '
            'group. When the rows of a view are requested, for example via the'
            '`list_database_table_grid_view_rows` endpoint, then only the rows that '
            'apply to all the filters are going to be returned. A filters compares the '
            'value of a field to the value of a filter. It depends on the type how '
            'values are going to be compared.'
        ),
        request=CreateViewFilterSerializer(),
        responses={
            200: ViewFilterSerializer(),
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP', 'ERROR_REQUEST_BODY_VALIDATION',
                'ERROR_FIELD_NOT_IN_TABLE', 'ERROR_VIEW_FILTER_NOT_SUPPORTED',
                'ERROR_VIEW_FILTER_TYPE_NOT_ALLOWED_FOR_FIELD'
            ]),
            404: get_error_schema(['ERROR_VIEW_DOES_NOT_EXIST'])
        }
    )
    @transaction.atomic
    @validate_body(CreateViewFilterSerializer)
    @map_exceptions({
        ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        FieldNotInTable: ERROR_FIELD_NOT_IN_TABLE,
        ViewFilterNotSupported: ERROR_VIEW_FILTER_NOT_SUPPORTED,
        ViewFilterTypeNotAllowedForField: ERROR_VIEW_FILTER_TYPE_NOT_ALLOWED_FOR_FIELD
    })
    def post(self, request, data, view_id):
        """Creates a new filter for the provided view."""

        view_handler = ViewHandler()
        view = view_handler.get_view(request.user, view_id)
        # We can safely assume the field exists because the CreateViewFilterSerializer
        # has already checked that.
        field = Field.objects.get(pk=data['field'])
        view_filter = view_handler.create_filter(request.user, view, field,
                                                 data['type'], data['value'])

        serializer = ViewFilterSerializer(view_filter)
        return Response(serializer.data)


class ViewFilterView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_filter_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Returns the view filter related to the provided value.'
            )
        ],
        tags=['Database table views'],
        operation_id='get_database_table_view_filter',
        description=(
            'Returns the existing view filter if the authorized user has access to the'
            'related database\'s group.'
        ),
        responses={
            200: ViewFilterSerializer(),
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema(['ERROR_VIEW_FILTER_DOES_NOT_EXIST'])
        }
    )
    @map_exceptions({
        ViewFilterDoesNotExist: ERROR_VIEW_FILTER_DOES_NOT_EXIST,
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, view_filter_id):
        """Selects a single filter and responds with a serialized version."""

        view_filter = ViewHandler().get_filter(request.user, view_filter_id)
        serializer = ViewFilterSerializer(view_filter)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_filter_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Updates the view filter related to the provided value.'
            )
        ],
        tags=['Database table views'],
        operation_id='update_database_table_view_filter',
        description=(
            'Updates the existing filter if the authorized user has access to the '
            'related database\'s group.'
        ),
        request=UpdateViewFilterSerializer(),
        responses={
            200: ViewFilterSerializer(),
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP', 'ERROR_FIELD_NOT_IN_TABLE',
                'ERROR_VIEW_FILTER_NOT_SUPPORTED',
                'ERROR_VIEW_FILTER_TYPE_NOT_ALLOWED_FOR_FIELD'
            ]),
            404: get_error_schema(['ERROR_VIEW_FILTER_DOES_NOT_EXIST'])
        }
    )
    @transaction.atomic
    @validate_body(UpdateViewFilterSerializer)
    @map_exceptions({
        ViewFilterDoesNotExist: ERROR_VIEW_FILTER_DOES_NOT_EXIST,
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        FieldNotInTable: ERROR_FIELD_NOT_IN_TABLE,
        ViewFilterTypeNotAllowedForField: ERROR_VIEW_FILTER_TYPE_NOT_ALLOWED_FOR_FIELD
    })
    def patch(self, request, data, view_filter_id):
        """Updates the view filter if the user belongs to the group."""

        handler = ViewHandler()
        view_filter = handler.get_filter(request.user, view_filter_id)

        if 'field' in data:
            # We can safely assume the field exists because the
            # UpdateViewFilterSerializer has already checked that.
            data['field'] = Field.objects.get(pk=data['field'])

        if 'type' in data:
            data['type_name'] = data.pop('type')

        view_filter = handler.update_filter(request.user, view_filter, **data)

        serializer = ViewFilterSerializer(view_filter)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_filter_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Deletes the filter related to the provided value.'
            )
        ],
        tags=['Database table views'],
        operation_id='delete_database_table_view_filter',
        description=(
            'Deletes the existing filter if the authorized user has access to the '
            'related database\'s group.'
        ),
        responses={
            204: None,
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema(['ERROR_VIEW_FILTER_DOES_NOT_EXIST'])
        }
    )
    @transaction.atomic
    @map_exceptions({
        ViewFilterDoesNotExist: ERROR_VIEW_FILTER_DOES_NOT_EXIST,
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def delete(self, request, view_filter_id):
        """Deletes an existing filter if the user belongs to the group."""

        view = ViewHandler().get_filter(request.user, view_filter_id)
        ViewHandler().delete_filter(request.user, view)

        return Response(status=204)

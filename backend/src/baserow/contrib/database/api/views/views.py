from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes

from baserow.api.decorators import (
    validate_body, validate_body_custom_fields, map_exceptions, allowed_includes
)
from baserow.api.utils import validate_data_custom_fields
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.utils import PolymorphicCustomFieldRegistrySerializer
from baserow.api.schemas import get_error_schema
from baserow.core.exceptions import UserNotInGroup
from baserow.contrib.database.api.fields.errors import ERROR_FIELD_NOT_IN_TABLE
from baserow.contrib.database.api.tables.errors import ERROR_TABLE_DOES_NOT_EXIST
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.exceptions import FieldNotInTable
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.views.registries import view_type_registry
from baserow.contrib.database.views.models import View, ViewFilter, ViewSort
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.exceptions import (
    ViewDoesNotExist, ViewFilterDoesNotExist, ViewFilterNotSupported,
    ViewFilterTypeNotAllowedForField, ViewSortDoesNotExist, ViewSortNotSupported,
    ViewSortFieldAlreadyExist, ViewSortFieldNotSupported
)

from .serializers import (
    ViewSerializer, CreateViewSerializer, UpdateViewSerializer, ViewFilterSerializer,
    CreateViewFilterSerializer, UpdateViewFilterSerializer, ViewSortSerializer,
    CreateViewSortSerializer, UpdateViewSortSerializer
)
from .errors import (
    ERROR_VIEW_DOES_NOT_EXIST, ERROR_VIEW_FILTER_DOES_NOT_EXIST,
    ERROR_VIEW_FILTER_NOT_SUPPORTED, ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD,
    ERROR_VIEW_SORT_DOES_NOT_EXIST, ERROR_VIEW_SORT_NOT_SUPPORTED,
    ERROR_VIEW_SORT_FIELD_ALREADY_EXISTS, ERROR_VIEW_SORT_FIELD_NOT_SUPPORTED
)


class ViewsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]

        return super().get_permissions()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='table_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Returns only views of the table related to the provided '
                            'value.'
            ),
            OpenApiParameter(
                name='include',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    'A comma separated list of extra attributes to include on each '
                    'view in the response. The supported attributes are `filters` and '
                    '`sortings`. For example `include=filters,sortings` will add the '
                    'attributes `filters` and `sortings` to every returned view, '
                    'containing a list of the views filters and sortings respectively.'
                )
            ),
        ],
        tags=['Database table views'],
        operation_id='list_database_table_views',
        description=(
            'Lists all views of the table related to the provided `table_id` if the '
            'user has access to the related database\'s group. If the group is '
            'related to a template, then this endpoint will be publicly accessible. A '
            'table can have multiple views. Each view can display the data in a '
            'different way. For example the `grid` view shows the in a spreadsheet '
            'like way. That type has custom endpoints for data retrieval and '
            'manipulation. In the future other views types like a calendar or Kanban '
            'are going to be added. Each type can have different properties.'
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
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP
    })
    @allowed_includes('filters', 'sortings')
    def get(self, request, table_id, filters, sortings):
        """
        Responds with a list of serialized views that belong to the table if the user
        has access to that group.
        """

        table = TableHandler().get_table(table_id)
        table.database.group.has_user(request.user, raise_error=True,
                                      allow_if_template=True)
        views = View.objects.filter(table=table).select_related('content_type')

        if filters:
            views = views.prefetch_related('viewfilter_set')

        if sortings:
            views = views.prefetch_related('viewsort_set')

        data = [
            view_type_registry.get_serializer(
                view,
                ViewSerializer,
                filters=filters,
                sortings=sortings
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
            ),
            OpenApiParameter(
                name='include',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    'A comma separated list of extra attributes to include on each '
                    'view in the response. The supported attributes are `filters` and '
                    '`sortings`. '
                    'For example `include=filters,sortings` will add the attributes '
                    '`filters` and `sortings` to every returned view, containing '
                    'a list of the views filters and sortings respectively.'
                )
            ),
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
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP
    })
    @allowed_includes('filters', 'sortings')
    def post(self, request, data, table_id, filters, sortings):
        """Creates a new view for a user."""

        table = TableHandler().get_table(table_id)
        view = ViewHandler().create_view(
            request.user, table, data.pop('type'), **data)

        serializer = view_type_registry.get_serializer(
            view,
            ViewSerializer,
            filters=filters,
            sortings=sortings
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
            ),
            OpenApiParameter(
                name='include',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    'A comma separated list of extra attributes to include on the '
                    'returned view. The supported attributes are are `filters` and '
                    '`sortings`. '
                    'For example `include=filters,sortings` will add the attributes '
                    '`filters` and `sortings` to every returned view, containing '
                    'a list of the views filters and sortings respectively.'
                )
            ),
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
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP
    })
    @allowed_includes('filters', 'sortings')
    def get(self, request, view_id, filters, sortings):
        """Selects a single view and responds with a serialized version."""

        view = ViewHandler().get_view(view_id)
        view.table.database.group.has_user(request.user, raise_error=True)
        serializer = view_type_registry.get_serializer(
            view,
            ViewSerializer,
            filters=filters,
            sortings=sortings
        )
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Updates the view related to the provided value.'
            ),
            OpenApiParameter(
                name='include',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    'A comma separated list of extra attributes to include on the '
                    'returned view. The supported attributes are are `filters` and '
                    '`sortings`. '
                    'For example `include=filters,sortings` will add the attributes '
                    '`filters` and `sortings` to every returned view, containing '
                    'a list of the views filters and sortings respectively.'
                )
            ),
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
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP
    })
    @allowed_includes('filters', 'sortings')
    def patch(self, request, view_id, filters, sortings):
        """Updates the view if the user belongs to the group."""

        view = ViewHandler().get_view(view_id).specific
        view_type = view_type_registry.get_by_model(view)
        data = validate_data_custom_fields(
            view_type.type, view_type_registry, request.data,
            base_serializer_class=UpdateViewSerializer
        )

        view = ViewHandler().update_view(request.user, view, **data)

        serializer = view_type_registry.get_serializer(
            view,
            ViewSerializer,
            filters=filters,
            sortings=sortings
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
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP
    })
    def delete(self, request, view_id):
        """Deletes an existing view if the user belongs to the group."""

        view = ViewHandler().get_view(view_id)
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
        tags=['Database table view filters'],
        operation_id='list_database_table_view_filters',
        description=(
            'Lists all filters of the view related to the provided `view_id` if the '
            'user has access to the related database\'s group. A view can have '
            'multiple filters. When all the rows are requested for the view only those '
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
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, view_id):
        """
        Responds with a list of serialized filters that belong to the view if the user
        has access to that group.
        """

        view = ViewHandler().get_view(view_id)
        view.table.database.group.has_user(request.user, raise_error=True)
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
        tags=['Database table view filters'],
        operation_id='create_database_table_view_filter',
        description=(
            'Creates a new filter for the view related to the provided `view_id` '
            'parameter if the authorized user has access to the related database\'s '
            'group. When the rows of a view are requested, for example via the '
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
                'ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD'
            ]),
            404: get_error_schema(['ERROR_VIEW_DOES_NOT_EXIST'])
        }
    )
    @transaction.atomic
    @validate_body(CreateViewFilterSerializer)
    @map_exceptions({
        ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        FieldNotInTable: ERROR_FIELD_NOT_IN_TABLE,
        ViewFilterNotSupported: ERROR_VIEW_FILTER_NOT_SUPPORTED,
        ViewFilterTypeNotAllowedForField: ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD
    })
    def post(self, request, data, view_id):
        """Creates a new filter for the provided view."""

        view_handler = ViewHandler()
        view = view_handler.get_view(view_id)
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
        tags=['Database table view filters'],
        operation_id='get_database_table_view_filter',
        description=(
            'Returns the existing view filter if the authorized user has access to the'
            ' related database\'s group.'
        ),
        responses={
            200: ViewFilterSerializer(),
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema(['ERROR_VIEW_FILTER_DOES_NOT_EXIST'])
        }
    )
    @map_exceptions({
        ViewFilterDoesNotExist: ERROR_VIEW_FILTER_DOES_NOT_EXIST,
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP
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
        tags=['Database table view filters'],
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
                'ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD'
            ]),
            404: get_error_schema(['ERROR_VIEW_FILTER_DOES_NOT_EXIST'])
        }
    )
    @transaction.atomic
    @validate_body(UpdateViewFilterSerializer)
    @map_exceptions({
        ViewFilterDoesNotExist: ERROR_VIEW_FILTER_DOES_NOT_EXIST,
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        FieldNotInTable: ERROR_FIELD_NOT_IN_TABLE,
        ViewFilterTypeNotAllowedForField: ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD
    })
    def patch(self, request, data, view_filter_id):
        """Updates the view filter if the user belongs to the group."""

        handler = ViewHandler()
        view_filter = handler.get_filter(
            request.user,
            view_filter_id,
            base_queryset=ViewFilter.objects.select_for_update()
        )

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
        tags=['Database table view filters'],
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
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP
    })
    def delete(self, request, view_filter_id):
        """Deletes an existing filter if the user belongs to the group."""

        view = ViewHandler().get_filter(request.user, view_filter_id)
        ViewHandler().delete_filter(request.user, view)

        return Response(status=204)


class ViewSortingsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Returns only sortings of the view related to the provided '
                            'value.'
            )
        ],
        tags=['Database table view sortings'],
        operation_id='list_database_table_view_sortings',
        description=(
            'Lists all sortings of the view related to the provided `view_id` if the '
            'user has access to the related database\'s group. A view can have '
            'multiple sortings. When all the rows are requested they will be in the '
            'desired order.'
        ),
        responses={
            200: ViewSortSerializer(many=True),
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema(['ERROR_VIEW_DOES_NOT_EXIST'])
        }
    )
    @map_exceptions({
        ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, view_id):
        """
        Responds with a list of serialized sortings that belong to the view if the user
        has access to that group.
        """

        view = ViewHandler().get_view(view_id)
        view.table.database.group.has_user(request.user, raise_error=True)
        sortings = ViewSort.objects.filter(view=view)
        serializer = ViewSortSerializer(sortings, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Creates a sort for the view related to the provided '
                            'value.'
            )
        ],
        tags=['Database table view sortings'],
        operation_id='create_database_table_view_sort',
        description=(
            'Creates a new sort for the view related to the provided `view_id` '
            'parameter if the authorized user has access to the related database\'s '
            'group. When the rows of a view are requested, for example via the '
            '`list_database_table_grid_view_rows` endpoint, they will be returned in '
            'the respected order defined by all the sortings.'
        ),
        request=CreateViewSortSerializer(),
        responses={
            200: ViewSortSerializer(),
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP', 'ERROR_REQUEST_BODY_VALIDATION',
                'ERROR_VIEW_SORT_NOT_SUPPORTED', 'ERROR_FIELD_NOT_IN_TABLE',
                'ERROR_VIEW_SORT_FIELD_ALREADY_EXISTS',
                'ERROR_VIEW_SORT_FIELD_NOT_SUPPORTED'
            ]),
            404: get_error_schema(['ERROR_VIEW_DOES_NOT_EXIST'])
        }
    )
    @transaction.atomic
    @validate_body(CreateViewSortSerializer)
    @map_exceptions({
        ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        FieldNotInTable: ERROR_FIELD_NOT_IN_TABLE,
        ViewSortNotSupported: ERROR_VIEW_SORT_NOT_SUPPORTED,
        ViewSortFieldAlreadyExist: ERROR_VIEW_SORT_FIELD_ALREADY_EXISTS,
        ViewSortFieldNotSupported: ERROR_VIEW_SORT_FIELD_NOT_SUPPORTED,
    })
    def post(self, request, data, view_id):
        """Creates a new sort for the provided view."""

        view_handler = ViewHandler()
        view = view_handler.get_view(view_id)
        # We can safely assume the field exists because the CreateViewSortSerializer
        # has already checked that.
        field = Field.objects.get(pk=data['field'])
        view_sort = view_handler.create_sort(request.user, view, field, data['order'])

        serializer = ViewSortSerializer(view_sort)
        return Response(serializer.data)


class ViewSortView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_sort_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Returns the view sort related to the provided value.'
            )
        ],
        tags=['Database table view sortings'],
        operation_id='get_database_table_view_sort',
        description=(
            'Returns the existing view sort if the authorized user has access to the'
            ' related database\'s group.'
        ),
        responses={
            200: ViewSortSerializer(),
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema(['ERROR_VIEW_SORT_DOES_NOT_EXIST'])
        }
    )
    @map_exceptions({
        ViewSortDoesNotExist: ERROR_VIEW_SORT_DOES_NOT_EXIST,
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, view_sort_id):
        """Selects a single sort and responds with a serialized version."""

        view_sort = ViewHandler().get_sort(request.user, view_sort_id)
        serializer = ViewSortSerializer(view_sort)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_sort_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Updates the view sort related to the provided value.'
            )
        ],
        tags=['Database table view sortings'],
        operation_id='update_database_table_view_sort',
        description=(
            'Updates the existing sort if the authorized user has access to the '
            'related database\'s group.'
        ),
        request=UpdateViewSortSerializer(),
        responses={
            200: ViewSortSerializer(),
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP', 'ERROR_FIELD_NOT_IN_TABLE',
                'ERROR_VIEW_SORT_FIELD_ALREADY_EXISTS'
            ]),
            404: get_error_schema(['ERROR_VIEW_SORT_DOES_NOT_EXIST'])
        }
    )
    @transaction.atomic
    @validate_body(UpdateViewSortSerializer)
    @map_exceptions({
        ViewSortDoesNotExist: ERROR_VIEW_SORT_DOES_NOT_EXIST,
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        FieldNotInTable: ERROR_FIELD_NOT_IN_TABLE,
        ViewSortFieldAlreadyExist: ERROR_VIEW_SORT_FIELD_ALREADY_EXISTS,
        ViewSortFieldNotSupported: ERROR_VIEW_SORT_FIELD_NOT_SUPPORTED,
    })
    def patch(self, request, data, view_sort_id):
        """Updates the view sort if the user belongs to the group."""

        handler = ViewHandler()
        view_sort = handler.get_sort(
            request.user,
            view_sort_id,
            base_queryset=ViewSort.objects.select_for_update()
        )

        if 'field' in data:
            # We can safely assume the field exists because the
            # UpdateViewSortSerializer has already checked that.
            data['field'] = Field.objects.get(pk=data['field'])

        view_sort = handler.update_sort(request.user, view_sort, **data)

        serializer = ViewSortSerializer(view_sort)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='view_sort_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='Deletes the sort related to the provided value.'
            )
        ],
        tags=['Database table view sortings'],
        operation_id='delete_database_table_view_sort',
        description=(
            'Deletes the existing sort if the authorized user has access to the '
            'related database\'s group.'
        ),
        responses={
            204: None,
            400: get_error_schema(['ERROR_USER_NOT_IN_GROUP']),
            404: get_error_schema(['ERROR_VIEW_SORT_DOES_NOT_EXIST'])
        }
    )
    @transaction.atomic
    @map_exceptions({
        ViewSortDoesNotExist: ERROR_VIEW_SORT_DOES_NOT_EXIST,
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP
    })
    def delete(self, request, view_sort_id):
        """Deletes an existing sort if the user belongs to the group."""

        view = ViewHandler().get_sort(request.user, view_sort_id)
        ViewHandler().delete_sort(request.user, view)

        return Response(status=204)

from decimal import Decimal

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import (
    allowed_includes,
    map_exceptions,
    validate_body,
    validate_query_parameters,
)
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.pagination import PageNumberPagination
from baserow.api.schemas import get_error_schema
from baserow.api.search.serializers import SearchQueryParamSerializer
from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.contrib.database.api.constants import SEARCH_MODE_API_PARAM
from baserow.contrib.database.api.fields.errors import (
    ERROR_FIELD_DOES_NOT_EXIST,
    ERROR_FIELD_NOT_IN_TABLE,
    ERROR_FILTER_FIELD_NOT_FOUND,
    ERROR_ORDER_BY_FIELD_NOT_FOUND,
    ERROR_ORDER_BY_FIELD_NOT_POSSIBLE,
)
from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_example_row_metadata_field_serializer,
    get_example_row_serializer_class,
    get_row_serializer_class,
)
from baserow.contrib.database.api.utils import get_include_exclude_field_ids
from baserow.contrib.database.api.views.errors import (
    ERROR_AGGREGATION_TYPE_DOES_NOT_EXIST,
    ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW,
    ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST,
    ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD,
)
from baserow.contrib.database.api.views.grid.serializers import (
    GridViewFieldOptionsSerializer,
)
from baserow.contrib.database.api.views.serializers import (
    FieldOptionsField,
    serialize_group_by_metadata,
)
from baserow.contrib.database.api.views.utils import get_public_view_authorization_token
from baserow.contrib.database.fields.exceptions import (
    FieldDoesNotExist,
    FieldNotInTable,
    FilterFieldNotFound,
    OrderByFieldNotFound,
    OrderByFieldNotPossible,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.utils import get_field_id_from_field_key
from baserow.contrib.database.rows.registries import row_metadata_registry
from baserow.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from baserow.contrib.database.views.exceptions import (
    AggregationTypeDoesNotExist,
    NoAuthorizationToPubliclySharedView,
    ViewDoesNotExist,
    ViewFilterTypeDoesNotExist,
    ViewFilterTypeNotAllowedForField,
)
from baserow.contrib.database.views.filters import AdHocFilters
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import GridView
from baserow.contrib.database.views.registries import (
    view_aggregation_type_registry,
    view_filter_type_registry,
    view_type_registry,
)
from baserow.contrib.database.views.signals import view_loaded
from baserow.core.exceptions import UserNotInWorkspace
from baserow.core.handler import CoreHandler
from baserow.core.utils import split_comma_separated_string

from .errors import ERROR_GRID_DOES_NOT_EXIST
from .schemas import (
    field_aggregation_response_schema,
    field_aggregations_response_schema,
)
from .serializers import GridViewFilterSerializer


def get_available_aggregation_type():
    return [f.type for f in view_aggregation_type_registry.get_all()]


class GridViewView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        return super().get_permissions()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="view_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only rows that belong to the related view's "
                "table.",
            ),
            OpenApiParameter(
                name="count",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
                description="If provided only the count will be returned.",
            ),
            OpenApiParameter(
                name="include",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "A comma separated list allowing the values of `field_options` and "
                    "`row_metadata` which will add the object/objects with the same "
                    "name to the response if included. The `field_options` object "
                    "contains user defined view settings for each field. For example "
                    "the field's width is included in here. The `row_metadata` object"
                    " includes extra row specific data on a per row basis."
                ),
            ),
            OpenApiParameter(
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines how many rows should be returned.",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Can only be used in combination with the `limit` "
                "parameter and defines from which offset the rows should "
                "be returned.",
            ),
            OpenApiParameter(
                name="page",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines which page of rows should be returned. Either "
                "the `page` or `limit` can be provided, not both.",
            ),
            OpenApiParameter(
                name="size",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Can only be used in combination with the `page` parameter "
                "and defines how many rows should be returned.",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="If provided only rows with data that matches the search "
                "query are going to be returned.",
            ),
            OpenApiParameter(
                name="filters",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "A JSON serialized string containing the filter tree to apply "
                    "to this view. The filter tree is a nested structure containing "
                    "the filters that need to be applied. \n\n"
                    "An example of a valid filter tree is the following:"
                    '`{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", '
                    '"value": "test"}]}`.\n\n'
                    f"The following filters are available: "
                    f'{", ".join(view_filter_type_registry.get_types())}.'
                    "Please note that by passing the filters parameter the "
                    "view filters saved for the view itself will be ignored."
                ),
            ),
            OpenApiParameter(
                name="filter__{field}__{filter}",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    f"The rows can optionally be filtered by the same view filters "
                    f"available for the views. Multiple filters can be provided if "
                    f"they follow the same format. The field and filter variable "
                    f"indicate how to filter and the value indicates where to filter "
                    f"on.\n\n"
                    "Please note that if the `filters` parameter is provided, "
                    "this parameter will be ignored. \n\n"
                    f"For example if you provide the following GET parameter "
                    f"`filter__field_1__equal=test` then only rows where the value of "
                    f"field_1 is equal to test are going to be returned.\n\n"
                    f"The following filters are available: "
                    f'{", ".join(view_filter_type_registry.get_types())}.'
                    "Please note that by passing the filter parameters the "
                    "view filters saved for the view itself will be ignored."
                ),
            ),
            OpenApiParameter(
                name="filter_type",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "`AND`: Indicates that the rows must match all the provided "
                    "filters.\n"
                    "`OR`: Indicates that the rows only have to match one of the "
                    "filters.\n\n"
                    "This works only if two or more filters are provided."
                    "Please note that if the `filters` parameter is provided, "
                    "this parameter will be ignored. \n\n"
                ),
            ),
            OpenApiParameter(
                name="order_by",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Optionally the rows can be ordered by provided field ids "
                "separated by comma. By default a field is ordered in ascending (A-Z) "
                "order, but by prepending the field with a '-' it can be ordered "
                "descending (Z-A).",
            ),
            OpenApiParameter(
                name="include_fields",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "All the fields are included in the response by default. You can "
                    "select a subset of fields by providing the fields query "
                    "parameter. If you for example provide the following GET "
                    "parameter `include_fields=field_1,field_2` then only the fields "
                    "with id `1` and id `2` are going to be selected and included in "
                    "the response."
                ),
            ),
            OpenApiParameter(
                name="exclude_fields",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "All the fields are included in the response by default. You can "
                    "select a subset of fields by providing the exclude_fields query "
                    "parameter. If you for example provide the following GET "
                    "parameter `exclude_fields=field_1,field_2` then the fields with "
                    "id `1` and id `2` are going to be excluded from the selection and "
                    "response. "
                ),
            ),
            SEARCH_MODE_API_PARAM,
        ],
        tags=["Database table grid view"],
        operation_id="list_database_table_grid_view_rows",
        description=(
            "Lists the requested rows of the view's table related to the provided "
            "`view_id` if the authorized user has access to the database's workspace. "
            "The response is paginated either by a limit/offset or page/size style. "
            "The style depends on the provided GET parameters. The properties of the "
            "returned rows depends on which fields the table has. For a complete "
            "overview of fields use the **list_database_table_fields** endpoint to "
            "list them all. In the example all field types are listed, but normally "
            "the number in field_{id} key is going to be the id of the field. "
            "The value is what the user has provided and the format of it depends on "
            "the fields type.\n"
            "\n"
            "The filters and sortings are automatically applied. To get a full "
            "overview of the applied filters and sortings you can use the "
            "`list_database_table_view_filters` and "
            "`list_database_table_view_sortings` endpoints."
        ),
        responses={
            200: get_example_pagination_serializer_class(
                get_example_row_serializer_class(
                    example_type="get", user_field_names=False
                ),
                additional_fields={
                    "field_options": FieldOptionsField(
                        serializer_class=GridViewFieldOptionsSerializer, required=False
                    ),
                    "row_metadata": get_example_row_metadata_field_serializer(),
                },
                serializer_name="PaginationSerializerWithGridViewFieldOptions",
            ),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_ORDER_BY_FIELD_NOT_FOUND",
                    "ERROR_ORDER_BY_FIELD_NOT_POSSIBLE",
                    "ERROR_FILTER_FIELD_NOT_FOUND",
                    "ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST",
                    "ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD",
                    "ERROR_FILTERS_PARAM_VALIDATION_ERROR",
                ]
            ),
            404: get_error_schema(
                ["ERROR_GRID_DOES_NOT_EXIST", "ERROR_FIELD_DOES_NOT_EXIST"]
            ),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_GRID_DOES_NOT_EXIST,
            OrderByFieldNotFound: ERROR_ORDER_BY_FIELD_NOT_FOUND,
            OrderByFieldNotPossible: ERROR_ORDER_BY_FIELD_NOT_POSSIBLE,
            FilterFieldNotFound: ERROR_FILTER_FIELD_NOT_FOUND,
            ViewFilterTypeDoesNotExist: ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST,
            ViewFilterTypeNotAllowedForField: ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD,
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
        }
    )
    @allowed_includes("field_options", "row_metadata")
    @validate_query_parameters(SearchQueryParamSerializer, return_validated=True)
    def get(self, request, view_id, field_options, row_metadata, query_params):
        """
        Lists all the rows of a grid view, paginated either by a page or offset/limit.
        If the limit get parameter is provided the limit/offset pagination will be used
        else the page number pagination.

        Optionally the field options can also be included in the response if the
        `field_options` are provided in the include GET parameter.
        """

        include_fields = request.GET.get("include_fields")
        exclude_fields = request.GET.get("exclude_fields")
        adhoc_filters = AdHocFilters.from_request(request)
        order_by = request.GET.get("order_by")

        view_handler = ViewHandler()
        view = view_handler.get_view_as_user(
            request.user,
            view_id,
            GridView,
            base_queryset=GridView.objects.prefetch_related(
                "viewsort_set", "viewgroupby_set"
            ),
        )
        view_type = view_type_registry.get_by_model(view)

        workspace = view.table.database.workspace
        CoreHandler().check_permissions(
            request.user,
            ListRowsDatabaseTableOperationType.type,
            workspace=workspace,
            context=view.table,
            allow_if_template=True,
        )
        field_ids = get_include_exclude_field_ids(
            view.table, include_fields, exclude_fields
        )

        model = view.table.get_model()
        queryset = view_handler.get_queryset(
            view,
            apply_sorts=order_by is None,
            apply_filters=not adhoc_filters.has_any_filters,
            search=query_params.get("search"),
            search_mode=query_params.get("search_mode"),
            model=model,
        )

        if order_by is not None:
            queryset = queryset.order_by_fields_string(order_by, False)

        if adhoc_filters.has_any_filters:
            queryset = adhoc_filters.apply_to_queryset(model, queryset)

        if "count" in request.GET:
            return Response({"count": queryset.count()})

        if LimitOffsetPagination.limit_query_param in request.GET:
            paginator = LimitOffsetPagination()
        else:
            paginator = PageNumberPagination()

        page = paginator.paginate_queryset(queryset, request, self)
        serializer_class = get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            field_ids=field_ids,
        )
        serializer = serializer_class(page, many=True)

        response = paginator.get_paginated_response(serializer.data)

        if view_type.can_group_by and view.viewgroupby_set.all():
            group_by_fields = [
                model._field_objects[group_by.field_id]["field"]
                for group_by in view.viewgroupby_set.all()
            ]
            group_by_metadata = view_handler.get_group_by_metadata_in_rows(
                group_by_fields, page, queryset
            )
            serialized_group_by_metadata = serialize_group_by_metadata(
                group_by_metadata
            )
            response.data.update(group_by_metadata=serialized_group_by_metadata)

        if field_options:
            context = {"fields": [o["field"] for o in model._field_objects.values()]}
            serializer_class = view_type.get_field_options_serializer_class(
                create_if_missing=True
            )
            response.data.update(**serializer_class(view, context=context).data)

        if row_metadata:
            row_metadata = row_metadata_registry.generate_and_merge_metadata_for_rows(
                request.user, view.table, (row.id for row in page)
            )
            response.data.update(row_metadata=row_metadata)

        view_loaded.send(
            sender=self,
            table=view.table,
            view=view,
            table_model=model,
            user=request.user,
        )
        return response

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="view_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                required=False,
                description="Returns only rows that belong to the related view's "
                "table.",
            )
        ],
        tags=["Database table grid view"],
        operation_id="filter_database_table_grid_view_rows",
        description=(
            "Lists only the rows and fields that match the request. Only the rows "
            "with the ids that are in the `row_ids` list are going to be returned. "
            "Same goes for the fields, only the fields with the ids in the "
            "`field_ids` are going to be returned. This endpoint could be used to "
            "refresh data after changes something. For example in the web frontend "
            "after changing a field type, the data of the related cells will be "
            "refreshed using this endpoint. In the example all field types are listed, "
            "but normally  the number in field_{id} key is going to be the id of the "
            "field. The value is what the user has provided and the format of it "
            "depends on the fields type."
        ),
        request=GridViewFilterSerializer,
        responses={
            200: get_example_row_serializer_class(
                example_type="get", user_field_names=False
            )(many=True),
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_REQUEST_BODY_VALIDATION"]
            ),
            404: get_error_schema(["ERROR_GRID_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_GRID_DOES_NOT_EXIST,
        }
    )
    @validate_body(GridViewFilterSerializer)
    def post(self, request, view_id, data):
        """
        Row filter endpoint that only lists the requested rows and optionally only the
        requested fields.
        """

        view = ViewHandler().get_view_as_user(request.user, view_id, GridView)
        CoreHandler().check_permissions(
            request.user,
            ListRowsDatabaseTableOperationType.type,
            workspace=view.table.database.workspace,
            context=view.table,
        )

        model = view.table.get_model(field_ids=data["field_ids"])
        results = model.objects.filter(pk__in=data["row_ids"])

        serializer_class = get_row_serializer_class(
            model, RowSerializer, is_response=True
        )
        serializer = serializer_class(results, many=True)
        return Response(serializer.data)


class GridViewFieldAggregationsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        return super().get_permissions()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="view_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Select the view you want the aggregations for.",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "If provided the aggregations are calculated only for matching "
                    "rows."
                ),
            ),
            OpenApiParameter(
                name="include",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "if `include` is set to `total`, the total row count will be "
                    "returned with the result."
                ),
            ),
            OpenApiParameter(
                name="filters",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "A JSON serialized string containing the filter tree to apply "
                    "for the aggregation. The filter tree is a nested structure containing "
                    "the filters that need to be applied. \n\n"
                    "An example of a valid filter tree is the following:"
                    '`{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", '
                    '"value": "test"}]}`.\n\n'
                    f"The following filters are available: "
                    f'{", ".join(view_filter_type_registry.get_types())}.'
                    "Please note that by passing the filters parameter the "
                    "view filters saved for the view itself will be ignored."
                ),
            ),
            OpenApiParameter(
                name="filter__{field}__{filter}",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    f"The aggregation can optionally be filtered by the same view filters "
                    f"available for the views. Multiple filters can be provided if "
                    f"they follow the same format. The field and filter variable "
                    f"indicate how to filter and the value indicates where to filter "
                    f"on.\n\n"
                    "Please note that if the `filters` parameter is provided, "
                    "this parameter will be ignored. \n\n"
                    f"For example if you provide the following GET parameter "
                    f"`filter__field_1__equal=test` then only rows where the value of "
                    f"field_1 is equal to test are going to be returned.\n\n"
                    f"The following filters are available: "
                    f'{", ".join(view_filter_type_registry.get_types())}.'
                    "Please note that by passing the filter parameters the "
                    "view filters saved for the view itself will be ignored."
                ),
            ),
            OpenApiParameter(
                name="filter_type",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "`AND`: Indicates that the aggregated rows must match all the provided "
                    "filters.\n"
                    "`OR`: Indicates that the aggregated rows only have to match one of the "
                    "filters.\n\n"
                    "This works only if two or more filters are provided."
                    "Please note that if the `filters` parameter is provided, "
                    "this parameter will be ignored. \n\n"
                ),
            ),
            SEARCH_MODE_API_PARAM,
        ],
        tags=["Database table grid view"],
        operation_id="get_database_table_grid_view_field_aggregations",
        description=(
            "Returns all field aggregations values previously defined for this grid "
            "view. If filters exist for this view, the aggregations are computed only "
            "on filtered rows."
            "You need to have read permissions on the view to request aggregations."
        ),
        responses={
            200: field_aggregations_response_schema,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_FILTER_FIELD_NOT_FOUND",
                    "ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST",
                    "ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD",
                    "ERROR_FILTERS_PARAM_VALIDATION_ERROR",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_GRID_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_GRID_DOES_NOT_EXIST,
            FilterFieldNotFound: ERROR_FILTER_FIELD_NOT_FOUND,
            ViewFilterTypeDoesNotExist: ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST,
            ViewFilterTypeNotAllowedForField: ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD,
        }
    )
    @allowed_includes("total")
    @validate_query_parameters(SearchQueryParamSerializer, return_validated=True)
    def get(self, request, view_id, total, query_params):
        """
        Returns the aggregation values for the specified view considering the filters
        and the search term defined for this grid view.
        Also returns the total count to be able to make percentage on client side if
        asked.
        """

        adhoc_filters = AdHocFilters.from_request(request)
        search = query_params.get("search")
        search_mode = query_params.get("search_mode")
        view_handler = ViewHandler()
        view = view_handler.get_view(view_id, GridView)

        # Compute aggregation
        # Note: we can't optimize model by giving a model with just
        # the aggregated field because we may need other fields for filtering
        result = view_handler.get_view_field_aggregations(
            request.user,
            view,
            with_total=total,
            search=search,
            search_mode=search_mode,
            adhoc_filters=adhoc_filters,
        )

        # Decimal("NaN") can't be serialized, therefore we have to replace it
        # with its literal string representation
        nan_replacement_value = "NaN"
        for field in result:
            if isinstance(result[field], Decimal) and result[field].is_nan():
                result[field] = nan_replacement_value

        return Response(result)


class GridViewFieldAggregationView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        return super().get_permissions()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="view_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Select the view you want the aggregation for.",
            ),
            OpenApiParameter(
                name="field_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The field id you want to aggregate",
            ),
            OpenApiParameter(
                name="type",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "The aggregation type you want. Available aggregation types: "
                )
                + ", ".join(get_available_aggregation_type()),
            ),
            OpenApiParameter(
                name="include",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "if `include` is set to `total`, the total row count will be "
                    "returned with the result."
                ),
            ),
        ],
        tags=["Database table grid view"],
        operation_id="get_database_table_grid_view_field_aggregation",
        description=(
            "Computes the aggregation of all the values for a specified field from the "
            "selected grid view. You must select the aggregation type by setting "
            "the `type` GET parameter. If filters are configured for the selected "
            "view, the aggregation is calculated only on filtered rows. "
            "You need to have read permissions on the view to request an aggregation."
        ),
        responses={
            200: field_aggregation_response_schema,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_AGGREGATION_TYPE_DOES_NOT_EXIST",
                    "ERROR_FIELD_NOT_IN_TABLE",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_FIELD_DOES_NOT_EXIST",
                    "ERROR_GRID_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_GRID_DOES_NOT_EXIST,
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            FieldNotInTable: ERROR_FIELD_NOT_IN_TABLE,
            AggregationTypeDoesNotExist: ERROR_AGGREGATION_TYPE_DOES_NOT_EXIST,
        }
    )
    @allowed_includes("total")
    def get(self, request, view_id, field_id, total):
        """
        Returns the aggregation value for the specified view/field considering
        the filters configured for this grid view.
        Also returns the total count to be able to make percentage on client side if
        asked.
        """

        view_handler = ViewHandler()
        view = view_handler.get_view(view_id, GridView)

        field_instance = FieldHandler().get_field(field_id)

        aggregation_type = request.GET.get("type")

        # Compute aggregation
        # Note: we can't optimize model by giving a model with just
        # the aggregated field because we may need other fields for filtering
        aggregations = view_handler.get_field_aggregations(
            request.user, view, [(field_instance, aggregation_type)], with_total=total
        )

        result = {
            "value": aggregations[field_instance.db_column],
        }

        if total:
            result["total"] = aggregations["total"]

        return Response(result)


class PublicGridViewRowsView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="slug",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                description="Returns only rows that belong to the related view.",
            ),
            OpenApiParameter(
                name="count",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
                description="If provided only the count will be returned.",
            ),
            OpenApiParameter(
                name="include",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "A comma separated list allowing the values of "
                    "`field_options` which will add the object/objects with the "
                    "same "
                    "name to the response if included. The `field_options` object "
                    "contains user defined view settings for each field. For "
                    "example the field's width is included in here."
                ),
            ),
            OpenApiParameter(
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines how many rows should be returned.",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Can only be used in combination with the `limit` "
                "parameter and defines from which offset the rows should "
                "be returned.",
            ),
            OpenApiParameter(
                name="page",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines which page of rows should be returned. Either "
                "the `page` or `limit` can be provided, not both.",
            ),
            OpenApiParameter(
                name="size",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Can only be used in combination with the `page` parameter "
                "and defines how many rows should be returned.",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="If provided only rows with data that matches the search "
                "query are going to be returned.",
            ),
            OpenApiParameter(
                name="order_by",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Optionally the rows can be ordered by provided field ids "
                "separated by comma. By default a field is ordered in ascending (A-Z) "
                "order, but by prepending the field with a '-' it can be ordered "
                "descending (Z-A).",
            ),
            OpenApiParameter(
                name="group_by",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Optionally the rows can be grouped by provided field ids "
                "separated by comma. By default no groups are applied. This doesn't "
                "actually responds with the rows groups, this is just what's needed "
                "for the Baserow group by feature.",
            ),
            OpenApiParameter(
                name="filters",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "A JSON serialized string containing the filter tree to apply "
                    "to this view. The filter tree is a nested structure containing "
                    "the filters that need to be applied. \n\n"
                    "Please note that if this parameter is provided, all other "
                    "`filter__{field}__{filter}` will be ignored, "
                    "as well as the `filter_type` parameter. \n\n"
                    "An example of a valid filter tree is the following:"
                    '`{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", '
                    '"value": "test"}]}`.\n\n'
                    f"The following filters are available: "
                    f'{", ".join(view_filter_type_registry.get_types())}.'
                ),
            ),
            OpenApiParameter(
                name="filter__{field}__{filter}",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    f"The rows can optionally be filtered by the same view filters "
                    f"available for the views. Multiple filters can be provided if "
                    f"they follow the same format. The field and filter variable "
                    f"indicate how to filter and the value indicates where to filter "
                    f"on.\n\n"
                    "Please note that if the `filters` parameter is provided, "
                    "this parameter will be ignored. \n\n"
                    f"For example if you provide the following GET parameter "
                    f"`filter__field_1__equal=test` then only rows where the value of "
                    f"field_1 is equal to test are going to be returned.\n\n"
                    f"The following filters are available: "
                    f'{", ".join(view_filter_type_registry.get_types())}.'
                ),
            ),
            OpenApiParameter(
                name="filter_type",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "`AND`: Indicates that the rows must match all the provided "
                    "filters.\n"
                    "`OR`: Indicates that the rows only have to match one of the "
                    "filters.\n\n"
                    "This works only if two or more filters are provided."
                    "Please note that if the `filters` parameter is provided, "
                    "this parameter will be ignored. \n\n"
                ),
            ),
            OpenApiParameter(
                name="include_fields",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "All the fields are included in the response by default. You can "
                    "select a subset of fields by providing the fields query "
                    "parameter. If you for example provide the following GET "
                    "parameter `include_fields=field_1,field_2` then only the fields "
                    "with id `1` and id `2` are going to be selected and included in "
                    "the response."
                ),
            ),
            OpenApiParameter(
                name="exclude_fields",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "All the fields are included in the response by default. You can "
                    "select a subset of fields by providing the exclude_fields query "
                    "parameter. If you for example provide the following GET "
                    "parameter `exclude_fields=field_1,field_2` then the fields with "
                    "id `1` and id `2` are going to be excluded from the selection and "
                    "response. "
                ),
            ),
            SEARCH_MODE_API_PARAM,
        ],
        tags=["Database table grid view"],
        operation_id="public_list_database_table_grid_view_rows",
        description=(
            "Lists the requested rows of the view's table related to the provided "
            "`slug` if the grid view is public."
            "The response is paginated either by a limit/offset or page/size style. "
            "The style depends on the provided GET parameters. The properties of the "
            "returned rows depends on which fields the table has. For a complete "
            "overview of fields use the **list_database_table_fields** endpoint to "
            "list them all. In the example all field types are listed, but normally "
            "the number in field_{id} key is going to be the id of the field. "
            "The value is what the user has provided and the format of it depends on "
            "the fields type.\n"
            "\n"
        ),
        responses={
            200: get_example_pagination_serializer_class(
                get_example_row_serializer_class(
                    example_type="get", user_field_names=False
                ),
                additional_fields={
                    "field_options": FieldOptionsField(
                        serializer_class=GridViewFieldOptionsSerializer, required=False
                    ),
                },
                serializer_name="PublicPaginationSerializerWithGridViewFieldOptions",
            ),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_ORDER_BY_FIELD_NOT_FOUND",
                    "ERROR_ORDER_BY_FIELD_NOT_POSSIBLE",
                    "ERROR_FILTER_FIELD_NOT_FOUND",
                    "ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST",
                    "ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD",
                    "ERROR_FILTERS_PARAM_VALIDATION_ERROR",
                ]
            ),
            401: get_error_schema(["ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW"]),
            404: get_error_schema(
                ["ERROR_GRID_DOES_NOT_EXIST", "ERROR_FIELD_DOES_NOT_EXIST"]
            ),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_GRID_DOES_NOT_EXIST,
            OrderByFieldNotFound: ERROR_ORDER_BY_FIELD_NOT_FOUND,
            OrderByFieldNotPossible: ERROR_ORDER_BY_FIELD_NOT_POSSIBLE,
            FilterFieldNotFound: ERROR_FILTER_FIELD_NOT_FOUND,
            ViewFilterTypeDoesNotExist: ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST,
            ViewFilterTypeNotAllowedForField: ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD,
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            NoAuthorizationToPubliclySharedView: ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW,
        }
    )
    @allowed_includes("field_options")
    @validate_query_parameters(SearchQueryParamSerializer, return_validated=True)
    def get(
        self, request: Request, slug: str, field_options: bool, query_params
    ) -> Response:
        """
        Lists all the rows of a grid view, paginated either by a page or offset/limit.
        If the limit get parameter is provided the limit/offset pagination will be used
        else the page number pagination.

        Optionally the field options can also be included in the response if the the
        `field_options` are provided in the include GET parameter.
        """

        search = query_params.get("search")
        search_mode = query_params.get("search_mode")
        order_by = request.GET.get("order_by")
        group_by = request.GET.get("group_by")
        include_fields = request.GET.get("include_fields")
        exclude_fields = request.GET.get("exclude_fields")
        adhoc_filters = AdHocFilters.from_request(request)

        count = "count" in request.GET

        view_handler = ViewHandler()
        view = view_handler.get_public_view_by_slug(
            request.user,
            slug,
            GridView,
            authorization_token=get_public_view_authorization_token(request),
        )
        view_type = view_type_registry.get_by_model(view)
        model = view.table.get_model()

        (
            queryset,
            field_ids,
            publicly_visible_field_options,
        ) = ViewHandler().get_public_rows_queryset_and_field_ids(
            view,
            search=search,
            search_mode=search_mode,
            order_by=order_by,
            group_by=group_by,
            include_fields=include_fields,
            exclude_fields=exclude_fields,
            adhoc_filters=adhoc_filters,
            table_model=model,
            view_type=view_type,
        )

        if count:
            return Response({"count": queryset.count()})

        if LimitOffsetPagination.limit_query_param in request.GET:
            paginator = LimitOffsetPagination()
        else:
            paginator = PageNumberPagination()

        page = paginator.paginate_queryset(queryset, request, self)
        serializer_class = get_row_serializer_class(
            model, RowSerializer, is_response=True, field_ids=field_ids
        )
        serializer = serializer_class(page, many=True)
        response = paginator.get_paginated_response(serializer.data)

        if field_options:
            context = {"field_options": publicly_visible_field_options}
            serializer_class = view_type.get_field_options_serializer_class(
                create_if_missing=False
            )
            response.data.update(**serializer_class(view, context=context).data)

        if group_by:
            group_by_fields = [
                # We can safely do this without having to check whether the
                # `group_by` input is valid because this has already been validated
                # by the `get_public_rows_queryset_and_field_ids`.
                model._field_objects[get_field_id_from_field_key(field_string, False)][
                    "field"
                ]
                for field_string in split_comma_separated_string(group_by)
            ]
            group_by_metadata = view_handler.get_group_by_metadata_in_rows(
                group_by_fields, page, queryset
            )
            serialized_group_by_metadata = serialize_group_by_metadata(
                group_by_metadata
            )
            response.data.update(group_by_metadata=serialized_group_by_metadata)

        return response

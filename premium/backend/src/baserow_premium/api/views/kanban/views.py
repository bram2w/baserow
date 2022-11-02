from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from baserow_premium.views.exceptions import KanbanViewHasNoSingleSelectField
from baserow_premium.views.handler import get_rows_grouped_by_single_select_field
from baserow_premium.views.models import KanbanView
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import allowed_includes, map_exceptions
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from baserow.contrib.database.api.views.errors import (
    ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW,
)
from baserow.contrib.database.api.views.utils import get_public_view_authorization_token
from baserow.contrib.database.fields.field_filters import (
    FILTER_TYPE_AND,
    FILTER_TYPE_OR,
)
from baserow.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from baserow.contrib.database.views.exceptions import (
    NoAuthorizationToPubliclySharedView,
    ViewDoesNotExist,
)
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.registries import view_type_registry
from baserow.core.exceptions import UserNotInGroup
from baserow.core.handler import CoreHandler

from .errors import (
    ERROR_INVALID_SELECT_OPTION_PARAMETER,
    ERROR_KANBAN_DOES_NOT_EXIST,
    ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD,
)
from .exceptions import InvalidSelectOptionParameter
from .serializers import KanbanViewExampleResponseSerializer
from .utils import prepare_kanban_view_parameters


class KanbanViewView(APIView):
    permission_classes = (AllowAny,)

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
                name="include",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Accepts `field_options` as value if the field options "
                "must also be included in the response.",
            ),
            OpenApiParameter(
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines how many rows should be returned by default. "
                "This value can be overwritten per select option.",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines from which offset the rows should be returned."
                "This value can be overwritten per select option.",
            ),
            OpenApiParameter(
                name="select_option",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "Accepts multiple `select_option` parameters. If not provided, the "
                    "rows of all select options will be returned. If one or more "
                    "`select_option` parameters are provided, then only the rows of "
                    "those will be included in the response. "
                    "`?select_option=1&select_option=null` will only include the rows "
                    "for both select option with id `1` and `null`. "
                    "`?select_option=1,10,20` will only include the rows of select "
                    "option id `1` with a limit of `10` and and offset of `20`."
                ),
            ),
        ],
        tags=["Database table kanban view"],
        operation_id="list_database_table_kanban_view_rows",
        description=(
            "Responds with serialized rows grouped by the view's single select field "
            "options if the user is authenticated and has access to the related "
            "group. Additional query parameters can be provided to control the "
            "`limit` and `offset` per select option."
            "\n\nThis is a **premium** feature."
        ),
        responses={
            200: KanbanViewExampleResponseSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD",
                    "ERROR_INVALID_SELECT_OPTION_PARAMETER",
                    "ERROR_FEATURE_NOT_AVAILABLE",
                ]
            ),
            404: get_error_schema(["ERROR_KANBAN_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_KANBAN_DOES_NOT_EXIST,
            KanbanViewHasNoSingleSelectField: (
                ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD
            ),
            InvalidSelectOptionParameter: ERROR_INVALID_SELECT_OPTION_PARAMETER,
        }
    )
    @allowed_includes("field_options")
    def get(self, request, view_id, field_options):
        """Responds with the rows grouped by the view's select option field value."""

        view_handler = ViewHandler()
        view = view_handler.get_view(view_id, KanbanView)
        group = view.table.database.group

        # We don't want to check if there is an active premium license if the group
        # is a template because that feature must then be available for demo purposes.
        if not group.has_template():
            LicenseHandler.raise_if_user_doesnt_have_feature(
                request.user, group, PREMIUM
            )

        CoreHandler().check_permissions(
            request.user,
            ListRowsDatabaseTableOperationType.type,
            group=group,
            context=view.table,
            allow_if_template=True,
        )
        single_select_option_field = view.single_select_field

        if not single_select_option_field:
            raise KanbanViewHasNoSingleSelectField(
                "The requested kanban view does not have a required single select "
                "option field."
            )

        (
            included_select_options,
            default_limit,
            default_offset,
        ) = prepare_kanban_view_parameters(request)

        model = view.table.get_model()
        serializer_class = get_row_serializer_class(
            model, RowSerializer, is_response=True
        )
        rows = get_rows_grouped_by_single_select_field(
            view=view,
            single_select_field=single_select_option_field,
            option_settings=included_select_options,
            default_limit=default_limit,
            default_offset=default_offset,
            model=model,
        )

        for key, value in rows.items():
            rows[key]["results"] = serializer_class(value["results"], many=True).data

        response = {"rows": rows}

        if field_options:
            view_type = view_type_registry.get_by_model(view)
            context = {"fields": [o["field"] for o in model._field_objects.values()]}
            serializer_class = view_type.get_field_options_serializer_class(
                create_if_missing=True
            )
            response.update(**serializer_class(view, context=context).data)

        return Response(response)


class PublicKanbanViewView(APIView):
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
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines how many rows should be returned by default. "
                "This value can be overwritten per select option.",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines from which offset the rows should be returned."
                "This value can be overwritten per select option.",
            ),
            OpenApiParameter(
                name="select_option",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "Accepts multiple `select_option` parameters. If not provided, the "
                    "rows of all select options will be returned. If one or more "
                    "`select_option` parameters are provided, then only the rows of "
                    "those will be included in the response. "
                    "`?select_option=1&select_option=null` will only include the rows "
                    "for both select option with id `1` and `null`. "
                    "`?select_option=1,10,20` will only include the rows of select "
                    "option id `1` with a limit of `10` and and offset of `20`."
                ),
            ),
        ],
        tags=["Database table kanban view"],
        operation_id="public_list_database_table_kanban_view_rows",
        description=(
            "Responds with serialized rows grouped by the view's single select field "
            "options related to the `slug` if the kanban view is publicly shared. "
            "Additional query parameters can be provided to control the `limit` and "
            "`offset` per select option. \n\nThis is a **premium** feature."
        ),
        responses={
            200: KanbanViewExampleResponseSerializer,
            401: get_error_schema(["ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW"]),
            400: get_error_schema(
                [
                    "ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD",
                    "ERROR_INVALID_SELECT_OPTION_PARAMETER",
                ]
            ),
            404: get_error_schema(["ERROR_KANBAN_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            ViewDoesNotExist: ERROR_KANBAN_DOES_NOT_EXIST,
            KanbanViewHasNoSingleSelectField: (
                ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD
            ),
            InvalidSelectOptionParameter: ERROR_INVALID_SELECT_OPTION_PARAMETER,
            NoAuthorizationToPubliclySharedView: (
                ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW
            ),
        }
    )
    @allowed_includes("field_options")
    def get(self, request, slug: str, field_options: bool):
        """@TODO"""

        filter_type = (
            FILTER_TYPE_OR
            if request.GET.get("filter_type", "AND").upper() == "OR"
            else FILTER_TYPE_AND
        )
        filter_object = {key: request.GET.getlist(key) for key in request.GET.keys()}

        view_handler = ViewHandler()
        view = view_handler.get_public_view_by_slug(
            request.user,
            slug,
            KanbanView,
            authorization_token=get_public_view_authorization_token(request),
        )

        single_select_option_field = view.single_select_field
        if not single_select_option_field:
            raise KanbanViewHasNoSingleSelectField(
                "The requested kanban view does not have a required single select "
                "option field."
            )

        (
            included_select_options,
            default_limit,
            default_offset,
        ) = prepare_kanban_view_parameters(request)

        model = view.table.get_model()
        view_type = view_type_registry.get_by_model(view)
        (
            queryset,
            field_ids,
            publicly_visible_field_options,
        ) = ViewHandler().get_public_rows_queryset_and_field_ids(
            view,
            filter_type=filter_type,
            filter_object=filter_object,
            table_model=model,
            view_type=view_type,
        )

        serializer_class = get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            field_ids=field_ids,
        )
        rows = get_rows_grouped_by_single_select_field(
            view=view,
            single_select_field=single_select_option_field,
            option_settings=included_select_options,
            default_limit=default_limit,
            default_offset=default_offset,
            model=model,
            base_queryset=queryset,
        )

        for key, value in rows.items():
            rows[key]["results"] = serializer_class(value["results"], many=True).data

        response = {"rows": rows}

        if field_options:
            context = {"field_options": publicly_visible_field_options}
            serializer_class = view_type.get_field_options_serializer_class(
                create_if_missing=True
            )
            response.update(**serializer_class(view, context=context).data)

        return Response(response)

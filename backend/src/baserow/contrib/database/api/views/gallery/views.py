from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, allowed_includes
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.contrib.database.api.rows.serializers import (
    get_example_row_serializer_class,
)
from baserow.contrib.database.api.rows.serializers import (
    get_row_serializer_class,
    RowSerializer,
)
from baserow.contrib.database.api.views.gallery.serializers import (
    GalleryViewFieldOptionsSerializer,
)
from baserow.contrib.database.api.views.serializers import FieldOptionsField
from baserow.contrib.database.views.exceptions import ViewDoesNotExist
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import GalleryView
from baserow.contrib.database.views.registries import view_type_registry
from baserow.core.exceptions import UserNotInGroup

from .errors import ERROR_GALLERY_DOES_NOT_EXIST
from .pagination import GalleryLimitOffsetPagination


class GalleryViewView(APIView):
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
                name="count",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.NONE,
                description="If provided only the count will be returned.",
            ),
            OpenApiParameter(
                name="include",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "A comma separated list allowing the values of `field_options` "
                    "which will add the object/objects with the same name to the "
                    "response if included. The `field_options` object contains user "
                    "defined view settings for each field. For example the field's "
                    "order is included in here."
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
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="If provided only rows with data that matches the search "
                "query are going to be returned.",
            ),
        ],
        tags=["Database table gallery view"],
        operation_id="list_database_table_gallery_view_rows",
        description=(
            "Lists the requested rows of the view's table related to the provided "
            "`view_id` if the authorized user has access to the database's group. "
            "The response is paginated by a limit/offset style."
        ),
        responses={
            200: get_example_pagination_serializer_class(
                get_example_row_serializer_class(add_id=True, user_field_names=False),
                additional_fields={
                    "field_options": FieldOptionsField(
                        serializer_class=GalleryViewFieldOptionsSerializer,
                        required=False,
                    ),
                },
                serializer_name="PaginationSerializerWithGalleryViewFieldOptions",
            ),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_GALLERY_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_GALLERY_DOES_NOT_EXIST,
        }
    )
    @allowed_includes("field_options")
    def get(self, request, view_id, field_options):
        """Lists the rows for the gallery view."""

        view_handler = ViewHandler()
        view = view_handler.get_view(view_id, GalleryView)
        view_type = view_type_registry.get_by_model(view)

        view.table.database.group.has_user(
            request.user, raise_error=True, allow_if_template=True
        )
        model = view.table.get_model()
        queryset = view_handler.get_queryset(view, None, model)

        if "count" in request.GET:
            return Response({"count": queryset.count()})

        paginator = GalleryLimitOffsetPagination()
        page = paginator.paginate_queryset(queryset, request, self)
        serializer_class = get_row_serializer_class(
            model, RowSerializer, is_response=True
        )
        serializer = serializer_class(page, many=True)

        response = paginator.get_paginated_response(serializer.data)

        if field_options:
            context = {"fields": [o["field"] for o in model._field_objects.values()]}
            serializer_class = view_type.get_field_options_serializer_class(
                create_if_missing=True
            )
            response.data.update(**serializer_class(view, context=context).data)

        return response

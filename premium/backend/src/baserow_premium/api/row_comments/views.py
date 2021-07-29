from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.pagination import PageNumberPagination
from baserow.api.schemas import get_error_schema
from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.contrib.database.api.rows.errors import ERROR_ROW_DOES_NOT_EXIST
from baserow.contrib.database.api.tables.errors import ERROR_TABLE_DOES_NOT_EXIST
from baserow.contrib.database.rows.exceptions import RowDoesNotExist
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.core.exceptions import UserNotInGroup
from baserow_premium.row_comments.handler import RowCommentHandler
from .serializers import RowCommentSerializer, RowCommentCreateSerializer


class RowCommentView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The table the row is in.",
            ),
            OpenApiParameter(
                name="row_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The row to get row comments for.",
            ),
            OpenApiParameter(
                name="page",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Selects which page of row comments should be returned.",
            ),
        ],
        tags=["Database table rows"],
        operation_id="get_row_comments",
        description="Returns all row comments for the specified table and row.",
        responses={
            200: get_example_pagination_serializer_class(RowCommentSerializer),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(
                [
                    "ERROR_TABLE_DOES_NOT_EXIST",
                    "ERROR_ROW_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            RowDoesNotExist: ERROR_ROW_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request, table_id, row_id):
        comments = RowCommentHandler.get_comments(request.user, table_id, row_id)

        paginator = PageNumberPagination(
            limit_page_size=settings.ROW_COMMENT_PAGE_SIZE_LIMIT
        )

        page = paginator.paginate_queryset(comments, request, self)
        serializer = RowCommentSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The table to find the row to comment on in.",
            ),
            OpenApiParameter(
                name="row_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The row to create a comment for.",
            ),
        ],
        tags=["Database table rows"],
        operation_id="create_row_comment",
        description="Creates a comment on the specified row.",
        request=RowCommentCreateSerializer,
        responses={
            200: RowCommentSerializer,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(
                [
                    "ERROR_TABLE_DOES_NOT_EXIST",
                    "ERROR_ROW_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            RowDoesNotExist: ERROR_ROW_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    @validate_body(RowCommentCreateSerializer)
    def post(self, request, table_id, row_id, data):
        new_row_comment = RowCommentHandler.create_comment(
            request.user, table_id, row_id, data["comment"]
        )
        return Response(RowCommentSerializer(new_row_comment).data)

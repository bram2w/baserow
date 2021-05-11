from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import validate_body, map_exceptions
from baserow.api.pagination import PageNumberPagination
from baserow.api.schemas import get_error_schema
from baserow_premium.api.user_admin.errors import (
    USER_ADMIN_INVALID_SORT_DIRECTION,
    USER_ADMIN_INVALID_SORT_ATTRIBUTE,
    USER_ADMIN_CANNOT_DEACTIVATE_SELF,
    USER_ADMIN_CANNOT_DELETE_SELF,
    USER_ADMIN_UNKNOWN_USER,
)
from baserow_premium.api.user_admin.serializers import (
    UserAdminUpdateSerializer,
    UserAdminResponseSerializer,
)
from baserow_premium.user_admin.exceptions import (
    CannotDeactivateYourselfException,
    CannotDeleteYourselfException,
    UserDoesNotExistException,
    InvalidSortDirectionException,
    InvalidSortAttributeException,
)
from baserow_premium.user_admin.handler import (
    UserAdminHandler,
    allowed_user_admin_sort_field_names,
)


class UsersAdminView(APIView):
    permission_classes = (IsAdminUser,)
    _valid_sortable_fields = ",".join(allowed_user_admin_sort_field_names())

    @extend_schema(
        tags=["Users"],
        operation_id="list_users",
        description="Returns all baserow users with detailed information on each user, "
        "if the requesting user has admin permissions.",
        parameters=[
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="If provided only users with a username that matches the "
                "search query will be returned.",
            ),
            OpenApiParameter(
                name="sorts",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="A comma separated string of user attributes to sort by, "
                "each attribute must be prefixed with `+` for a descending "
                "sort or a `-` for an ascending sort. The accepted attribute names "
                f"are: {_valid_sortable_fields}. "
                "For example `sorts=-username,+is_active` will sort the "
                "results first by descending username and then ascending is_active."
                "A sort parameter with multiple instances of the same "
                "sort attribute will respond with the USER_ADMIN_INVALID_SORT_ATTRIBUTE"
                "error.",
            ),
            OpenApiParameter(
                name="page",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines which page of users should be returned.",
            ),
            OpenApiParameter(
                name="size",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines how many users should be returned per page.",
            ),
        ],
        responses={
            200: UserAdminResponseSerializer(many=True),
            400: get_error_schema(
                [
                    "ERROR_PAGE_SIZE_LIMIT",
                    "ERROR_INVALID_PAGE",
                    "USER_ADMIN_INVALID_SORT_DIRECTION",
                    "USER_ADMIN_INVALID_SORT_ATTRIBUTE",
                ]
            ),
            401: None,
        },
    )
    @map_exceptions(
        {
            InvalidSortDirectionException: USER_ADMIN_INVALID_SORT_DIRECTION,
            InvalidSortAttributeException: USER_ADMIN_INVALID_SORT_ATTRIBUTE,
        }
    )
    def get(self, request):
        """
        Lists all the users of a user, optionally filtering on username by the
        'search' get parameter, optionally sorting by the 'sorts' get parameter.
        """

        search = request.GET.get("search")
        sorts = request.GET.get("sorts")

        handler = UserAdminHandler()
        users = handler.get_users(request.user, search, sorts)

        paginator = PageNumberPagination(limit_page_size=100)
        page = paginator.paginate_queryset(users, request, self)
        serializer = UserAdminResponseSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


class UserAdminView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Users"],
        request=UserAdminUpdateSerializer,
        operation_id="edit_user",
        description=f"Updates specified user attributes and returns the updated user if"
        f" the requesting user has admin permissions. You cannot update yourself to no "
        f"longer be an admin or active.",
        parameters=[
            OpenApiParameter(
                name="user_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the user to edit",
            ),
        ],
        responses={
            200: UserAdminResponseSerializer(),
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "USER_ADMIN_CANNOT_DEACTIVATE_SELF",
                    "USER_ADMIN_UNKNOWN_USER",
                ]
            ),
            401: None,
        },
    )
    @validate_body(UserAdminUpdateSerializer, partial=True)
    @map_exceptions(
        {
            CannotDeactivateYourselfException: USER_ADMIN_CANNOT_DEACTIVATE_SELF,
            UserDoesNotExistException: USER_ADMIN_UNKNOWN_USER,
        }
    )
    @transaction.atomic
    def patch(self, request, user_id, data):
        """
        Updates the specified user with the supplied attributes. Will raise an exception
        if you attempt un-staff or de-activate yourself.
        """

        user_id = int(user_id)

        handler = UserAdminHandler()
        user = handler.update_user(request.user, user_id, **data)

        return Response(UserAdminResponseSerializer(user).data)

    @extend_schema(
        tags=["Users"],
        operation_id="delete_user",
        description="Deletes the specified user, if the requesting user has admin "
        "permissions. You cannot delete yourself.",
        parameters=[
            OpenApiParameter(
                name="user_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the user to delete",
            ),
        ],
        responses={
            200: None,
            400: get_error_schema(
                [
                    "USER_ADMIN_CANNOT_DELETE_SELF",
                    "USER_ADMIN_UNKNOWN_USER",
                ]
            ),
            401: None,
        },
    )
    @map_exceptions(
        {
            CannotDeleteYourselfException: USER_ADMIN_CANNOT_DELETE_SELF,
            UserDoesNotExistException: USER_ADMIN_UNKNOWN_USER,
        }
    )
    def delete(self, request, user_id):
        """
        Deletes the specified user. Raises an exception if you attempt to delete
        yourself.
        """

        user_id = int(user_id)

        handler = UserAdminHandler()
        handler.delete_user(request.user, user_id)

        return Response()

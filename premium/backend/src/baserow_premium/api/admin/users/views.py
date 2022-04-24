import logging
from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.status import HTTP_201_CREATED
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.views import ImpersonateJSONWebTokenView
from rest_framework_jwt.serializers import ImpersonateAuthTokenSerializer

from baserow.api.decorators import validate_body, map_exceptions
from baserow.api.schemas import get_error_schema
from baserow.api.user.schemas import authenticate_user_schema

from baserow_premium.api.admin.users.errors import (
    USER_ADMIN_CANNOT_DEACTIVATE_SELF,
    USER_ADMIN_CANNOT_DELETE_SELF,
    USER_ADMIN_UNKNOWN_USER,
)
from baserow_premium.api.admin.users.serializers import (
    UserAdminUpdateSerializer,
    UserAdminResponseSerializer,
)
from baserow_premium.admin.users.exceptions import (
    CannotDeactivateYourselfException,
    CannotDeleteYourselfException,
    UserDoesNotExistException,
)
from baserow_premium.admin.users.handler import UserAdminHandler


from django.contrib.auth import get_user_model

from baserow_premium.api.admin.views import AdminListingView
from baserow_premium.license.handler import check_active_premium_license

from .serializers import BaserowImpersonateAuthTokenSerializer


logger = logging.getLogger(__name__)
User = get_user_model()


class UsersAdminView(AdminListingView):
    serializer_class = UserAdminResponseSerializer
    search_fields = ["username"]
    sort_field_mapping = {
        "id": "id",
        "is_active": "is_active",
        "name": "first_name",
        "username": "username",
        "date_joined": "date_joined",
        "last_login": "last_login",
    }

    def get_queryset(self, request):
        return User.objects.prefetch_related(
            "groupuser_set", "groupuser_set__group"
        ).all()

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_list_users",
        description="Returns all users with detailed information on each user, "
        "if the requesting user is staff. \n\nThis is a **premium** feature.",
        **AdminListingView.get_extend_schema_parameters(
            "users", serializer_class, search_fields, sort_field_mapping
        ),
    )
    def get(self, request):
        check_active_premium_license(request.user)
        return super().get(request)


class UserAdminView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Admin"],
        request=UserAdminUpdateSerializer,
        operation_id="admin_edit_user",
        description=f"Updates specified user attributes and returns the updated user if"
        f" the requesting user is staff. You cannot update yourself to no longer be an "
        f"admin or active. \n\nThis is a **premium** feature.",
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
                    "ERROR_NO_ACTIVE_PREMIUM_LICENSE",
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
        tags=["Admin"],
        operation_id="admin_delete_user",
        description="Deletes the specified user, if the requesting user has admin "
        "permissions. You cannot delete yourself. \n\nThis is a **premium** feature.",
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
                    "ERROR_NO_ACTIVE_PREMIUM_LICENSE",
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
    @transaction.atomic
    def delete(self, request, user_id):
        """
        Deletes the specified user. Raises an exception if you attempt to delete
        yourself.
        """

        user_id = int(user_id)

        handler = UserAdminHandler()
        handler.delete_user(request.user, user_id)

        return Response(status=204)


class UserAdminImpersonateView(ImpersonateJSONWebTokenView):
    permission_classes = (IsAdminUser,)
    serializer_class = BaserowImpersonateAuthTokenSerializer

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_impersonate_user",
        description=(
            "This endpoint allows staff to impersonate another user by requesting a "
            "JWT token and user object. The requesting user must have staff access in "
            "order to do this. It's not possible to impersonate a superuser or staff."
            "\n\nThis is a **premium** feature."
        ),
        request=ImpersonateAuthTokenSerializer,
        responses={
            200: authenticate_user_schema,
        },
    )
    @map_exceptions(
        {
            CannotDeleteYourselfException: USER_ADMIN_CANNOT_DELETE_SELF,
            UserDoesNotExistException: USER_ADMIN_UNKNOWN_USER,
        }
    )
    def post(self, request):
        check_active_premium_license(request.user)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data.get("token")
        user = serializer.validated_data.get("user")

        response = JSONWebTokenAuthentication.jwt_create_response_payload(
            token=token, user=user, request=request
        )

        logger.info(
            f"{request.user.username} ({request.user.id}) requested an "
            f"impersonate token for {user.username} ({user.id})."
        )

        return Response(response, status=HTTP_201_CREATED)

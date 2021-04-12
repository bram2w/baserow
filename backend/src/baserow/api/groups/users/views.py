from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes

from baserow.api.decorators import validate_body, map_exceptions
from baserow.api.errors import (
    ERROR_GROUP_DOES_NOT_EXIST,
    ERROR_USER_NOT_IN_GROUP,
    ERROR_USER_INVALID_GROUP_PERMISSIONS,
)
from baserow.api.groups.users.errors import ERROR_GROUP_USER_DOES_NOT_EXIST
from baserow.api.schemas import get_error_schema
from baserow.core.models import GroupUser
from baserow.core.handler import CoreHandler
from baserow.core.exceptions import (
    UserNotInGroup,
    UserInvalidGroupPermissionsError,
    GroupDoesNotExist,
    GroupUserDoesNotExist,
)

from .serializers import (
    GroupUserSerializer,
    GroupUserGroupSerializer,
    UpdateGroupUserSerializer,
)


class GroupUsersView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the group user related to the provided value.",
            )
        ],
        tags=["Groups"],
        operation_id="list_group_users",
        description=(
            "Lists all the users that are in a group if the authorized user has admin "
            "permissions to the related group. To add a user to a group an invitation "
            "must be send first."
        ),
        responses={
            200: GroupUserSerializer(many=True),
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_USER_INVALID_GROUP_PERMISSIONS"]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def get(self, request, group_id):
        """Responds with a list of serialized users that are part of the group."""

        group = CoreHandler().get_group(group_id)
        group.has_user(request.user, "ADMIN", True)
        group_users = GroupUser.objects.filter(group=group).select_related("group")
        serializer = GroupUserSerializer(group_users, many=True)
        return Response(serializer.data)


class GroupUserView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_user_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the group user related to the provided value.",
            )
        ],
        tags=["Groups"],
        operation_id="update_group_user",
        description=(
            "Updates the existing group user related to the provided "
            "`group_user_id` param if the authorized user has admin rights to "
            "the related group."
        ),
        request=UpdateGroupUserSerializer,
        responses={
            200: GroupUserGroupSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_USER_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(UpdateGroupUserSerializer)
    @map_exceptions(
        {
            GroupUserDoesNotExist: ERROR_GROUP_USER_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def patch(self, request, data, group_user_id):
        """Updates the group user if the user has admin permissions to the group."""

        group_user = CoreHandler().get_group_user(
            group_user_id, base_queryset=GroupUser.objects.select_for_update()
        )
        group_user = CoreHandler().update_group_user(request.user, group_user, **data)
        return Response(GroupUserGroupSerializer(group_user).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_user_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Deletes the group user related to the provided " "value.",
            )
        ],
        tags=["Groups"],
        operation_id="delete_group_user",
        description=(
            "Deletes a group user if the authorized user has admin rights to "
            "the related group."
        ),
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_USER_INVALID_GROUP_PERMISSIONS"]
            ),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            GroupUserDoesNotExist: ERROR_GROUP_USER_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def delete(self, request, group_user_id):
        """Deletes an existing group_user if the user belongs to the group."""

        group_user = CoreHandler().get_group_user(
            group_user_id, base_queryset=GroupUser.objects.select_for_update()
        )
        CoreHandler().delete_group_user(request.user, group_user)
        return Response(status=204)

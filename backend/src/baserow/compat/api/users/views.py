from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema

from baserow.api.decorators import (
    map_exceptions,
    validate_body,
    validate_query_parameters,
)
from baserow.api.errors import (
    ERROR_GROUP_DOES_NOT_EXIST,
    ERROR_INVALID_SORT_ATTRIBUTE,
    ERROR_INVALID_SORT_DIRECTION,
    ERROR_USER_INVALID_GROUP_PERMISSIONS,
    ERROR_USER_NOT_IN_GROUP,
)
from baserow.api.exceptions import (
    InvalidSortAttributeException,
    InvalidSortDirectionException,
)
from baserow.api.schemas import get_error_schema
from baserow.api.workspaces.users.errors import (
    ERROR_CANNOT_DELETE_YOURSELF_FROM_GROUP,
    ERROR_GROUP_USER_DOES_NOT_EXIST,
)
from baserow.api.workspaces.users.serializers import (
    GetWorkspaceUsersViewParamsSerializer,
    UpdateWorkspaceUserSerializer,
    WorkspaceUserSerializer,
    get_list_workspace_user_serializer,
)
from baserow.api.workspaces.users.views import WorkspaceUsersView, WorkspaceUserView
from baserow.compat.api.conf import (
    GROUP_USER_DEPRECATION_PREFIXES as DEPRECATION_PREFIXES,
)
from baserow.core.exceptions import (
    CannotDeleteYourselfFromWorkspace,
    UserInvalidWorkspacePermissionsError,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
    WorkspaceUserDoesNotExist,
)

ListWorkspaceUsersWithMemberDataSerializer = get_list_workspace_user_serializer()


class GroupUsersCompatView(WorkspaceUsersView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Lists group users related to the provided group value.",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Search for group users by username, or email.",
            ),
            OpenApiParameter(
                name="sorts",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Sort group users by name, email or role.",
            ),
        ],
        tags=["Groups"],
        deprecated=True,
        operation_id="list_group_users",
        description=(
            f"{DEPRECATION_PREFIXES['list_group_users']} Lists all the users that "
            "are in a group if the authorized user has admin permissions to the "
            "related group. To add a user to a group an invitation must be sent first."
        ),
        responses={
            200: ListWorkspaceUsersWithMemberDataSerializer(many=True),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                    "ERROR_INVALID_SORT_DIRECTION",
                    "ERROR_INVALID_SORT_ATTRIBUTE",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserInvalidWorkspacePermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
            InvalidSortDirectionException: ERROR_INVALID_SORT_DIRECTION,
            InvalidSortAttributeException: ERROR_INVALID_SORT_ATTRIBUTE,
        }
    )
    @validate_query_parameters(GetWorkspaceUsersViewParamsSerializer)
    def get(self, request, group_id, query_params):
        """Responds with a list of serialized users that are part of the group."""

        return super().get(request, workspace_id=group_id)


class GroupUserCompatView(WorkspaceUserView):
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
        deprecated=True,
        operation_id="update_group_user",
        description=(
            f"{DEPRECATION_PREFIXES['update_group_user']} Updates the existing group "
            "user related to the provided `group_user_id` param if the authorized "
            "user has admin rights to the related group."
        ),
        request=UpdateWorkspaceUserSerializer,
        responses={
            200: WorkspaceUserSerializer,
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
    @validate_body(UpdateWorkspaceUserSerializer)
    @map_exceptions(
        {
            WorkspaceUserDoesNotExist: ERROR_GROUP_USER_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserInvalidWorkspacePermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def patch(self, request, data, group_user_id):
        """
        Updates the group user if the user has admin permissions to the group.
        """

        return super().patch(request, workspace_user_id=group_user_id)

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
        deprecated=True,
        operation_id="delete_group_user",
        description=(
            f"{DEPRECATION_PREFIXES['delete_group_user']} Deletes a group user if the "
            "authorized user has admin rights to the related group."
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
            WorkspaceUserDoesNotExist: ERROR_GROUP_USER_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserInvalidWorkspacePermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
            CannotDeleteYourselfFromWorkspace: ERROR_CANNOT_DELETE_YOURSELF_FROM_GROUP,
        }
    )
    def delete(self, request, group_user_id):
        """Deletes an existing group_user if the user belongs to the group."""

        return super().delete(request, workspace_user_id=group_user_id)

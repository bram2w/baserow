from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import (
    ERROR_GROUP_DOES_NOT_EXIST,
    ERROR_USER_INVALID_GROUP_PERMISSIONS,
    ERROR_USER_NOT_IN_GROUP,
)
from baserow.api.schemas import (
    CLIENT_SESSION_ID_SCHEMA_PARAMETER,
    CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
    get_error_schema,
)
from baserow.api.trash.errors import ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM
from baserow.api.workspaces.serializers import (
    OrderWorkspacesSerializer,
    PermissionObjectSerializer,
    WorkspaceSerializer,
)
from baserow.api.workspaces.users.serializers import WorkspaceUserWorkspaceSerializer
from baserow.api.workspaces.views import (
    WorkspaceLeaveView,
    WorkspaceOrderView,
    WorkspacePermissionsView,
    WorkspacesView,
    WorkspaceView,
)
from baserow.compat.api.conf import GROUP_DEPRECATION_PREFIXES as DEPRECATION_PREFIXES
from baserow.core.exceptions import (
    UserInvalidWorkspacePermissionsError,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
)
from baserow.core.trash.exceptions import CannotDeleteAlreadyDeletedItem


class GroupsCompatView(WorkspacesView):
    @extend_schema(
        tags=["Groups"],
        deprecated=True,
        operation_id="list_groups",
        description=(
            f"{DEPRECATION_PREFIXES['list_groups']} Lists all the groups of the "
            "authorized user. A group can contain multiple applications like a "
            "database. Multiple users can have access to a group. For example each "
            "company could have their own group containing databases related to that "
            "company. The order of the groups are custom for each user. The order is "
            "configurable via the **order_groups** endpoint."
        ),
        responses={200: WorkspaceUserWorkspaceSerializer(many=True)},
    )
    def get(self, request):
        """
        Responds with a list of serialized groups where the user is part of.
        """

        return super().get(request)

    @extend_schema(
        tags=["Groups"],
        deprecated=True,
        operation_id="create_group",
        parameters=[CLIENT_SESSION_ID_SCHEMA_PARAMETER],
        description=(
            f"{DEPRECATION_PREFIXES['create_group']} Creates a new group where only "
            "the authorized user has access to. No initial data like database "
            "applications are added, they have to be created via other endpoints."
        ),
        request=WorkspaceSerializer,
        responses={200: WorkspaceUserWorkspaceSerializer},
    )
    @map_exceptions()
    @transaction.atomic
    @validate_body(WorkspaceSerializer)
    def post(self, request, data):
        """Creates a new group for a user."""

        return super().post(request)


class GroupCompatView(WorkspaceView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the group related to the provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Groups"],
        deprecated=True,
        operation_id="update_group",
        description=(
            f"{DEPRECATION_PREFIXES['update_group']} Updates the existing group "
            "related to the provided `group_id` parameter if the authorized user "
            "belongs to the group. It is not yet possible to add additional users "
            "to a group."
        ),
        request=WorkspaceSerializer,
        responses={
            200: WorkspaceSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(WorkspaceSerializer)
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserInvalidWorkspacePermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def patch(self, request, data, group_id):
        """Updates the group if it belongs to a user."""

        return super().patch(request, workspace_id=group_id)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Deletes the group related to the provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Groups"],
        deprecated=True,
        operation_id="delete_group",
        description=(
            f"{DEPRECATION_PREFIXES['delete_group']} Deletes an existing group if the "
            "authorized user belongs to the group. All the applications, databases, "
            "tables etc that were in the group are going to be deleted also."
        ),
        request=WorkspaceSerializer,
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                    "ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserInvalidWorkspacePermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
            CannotDeleteAlreadyDeletedItem: ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM,
        }
    )
    @extend_schema(exclude=True, deprecated=True)
    def delete(self, request, group_id: int):
        """Deletes an existing group if it belongs to a user."""

        return super().delete(request, group_id)


class GroupLeaveCompatView(WorkspaceLeaveView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Leaves the group related to the value.",
            )
        ],
        tags=["Groups"],
        deprecated=True,
        operation_id="leave_group",
        description=(
            f"{DEPRECATION_PREFIXES['leave_group']} Makes the authenticated user leave "
            "the group related to the provided `group_id` if the user is in that "
            "group. If the user is the last admin in the group, they will not be able to "
            "leave it. There must always be one admin in the group, otherwise it will "
            "be left without control. If that is the case, they must either delete the "
            "group or give another member admin permissions first."
        ),
        request=None,
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_GROUP_USER_IS_LAST_ADMIN"]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    def post(self, request, group_id):
        """Leaves the group if the user is a member of it."""

        return super().post(request, group_id)


class GroupOrderCompatView(WorkspaceOrderView):
    @extend_schema(
        parameters=[
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Groups"],
        deprecated=True,
        operation_id="order_groups",
        description=(
            f"{DEPRECATION_PREFIXES['order_groups']} Changes the order of the provided "
            "group ids to the matching position that the id has in the list. If the "
            "authorized user does not belong to the group it will be ignored. "
            "The order will be custom for each user."
        ),
        request=OrderWorkspacesSerializer,
        responses={
            204: None,
        },
    )
    @transaction.atomic
    @validate_body(OrderWorkspacesSerializer)
    def post(self, request, data):
        """Updates to order of some groups for a user."""

        return super().post(request)


class GroupPermissionsCompatView(WorkspacePermissionsView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The group id we want the permission object for.",
            ),
        ],
        tags=["Groups"],
        deprecated=True,
        operation_id="group_permissions",
        description=(
            f"{DEPRECATION_PREFIXES['group_permissions']} Returns a the permission "
            "data necessary to determine the permissions of a specific user over a "
            "specific group.\n See `core.handler.CoreHandler.get_permissions()` "
            "for more details."
        ),
        responses={
            200: PermissionObjectSerializer(many=True),
            404: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_GROUP_DOES_NOT_EXIST"]
            ),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request, group_id):
        """
        Returns the permission object for the given workspace.
        """

        return super().get(request, group_id)

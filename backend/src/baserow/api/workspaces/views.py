from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
from baserow.api.workspaces.users.serializers import WorkspaceUserWorkspaceSerializer
from baserow.core.action.registries import action_type_registry
from baserow.core.actions import (
    CreateWorkspaceActionType,
    DeleteWorkspaceActionType,
    LeaveWorkspaceActionType,
    OrderWorkspacesActionType,
    UpdateWorkspaceActionType,
)
from baserow.core.exceptions import (
    UserInvalidWorkspacePermissionsError,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
    WorkspaceUserIsLastAdmin,
)
from baserow.core.handler import CoreHandler
from baserow.core.notifications.handler import NotificationHandler
from baserow.core.trash.exceptions import CannotDeleteAlreadyDeletedItem

from .errors import ERROR_GROUP_USER_IS_LAST_ADMIN
from .serializers import (
    OrderWorkspacesSerializer,
    PermissionObjectSerializer,
    WorkspaceSerializer,
)


class WorkspacesView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Workspaces"],
        operation_id="list_workspaces",
        description=(
            "Lists all the workspaces of the authorized user. A workspace can contain "
            "multiple applications like a database. Multiple users can have "
            "access to a workspace. For example each company could have their own workspace "
            "containing databases related to that company. The order of the workspaces "
            "are custom for each user. The order is configurable via the "
            "**order_workspaces** endpoint."
        ),
        responses={200: WorkspaceUserWorkspaceSerializer(many=True)},
    )
    def get(self, request):
        """Responds with a list of serialized workspaces where the user is part of."""

        workspaceuser_workspaces = (
            CoreHandler()
            .get_workspaceuser_workspace_queryset()
            .filter(user=request.user)
        )

        workspaceuser_workspaces = (
            NotificationHandler.annotate_workspaces_with_unread_notifications_count(
                request.user, workspaceuser_workspaces, outer_ref_key="workspace_id"
            )
        )

        serializer = WorkspaceUserWorkspaceSerializer(
            workspaceuser_workspaces, many=True
        )
        return Response(serializer.data)

    @extend_schema(
        parameters=[CLIENT_SESSION_ID_SCHEMA_PARAMETER],
        tags=["Workspaces"],
        operation_id="create_workspace",
        description=(
            "Creates a new workspace where only the authorized user has access to. No "
            "initial data like database applications are added, they have to be "
            "created via other endpoints."
        ),
        request=WorkspaceSerializer,
        responses={200: WorkspaceUserWorkspaceSerializer},
    )
    @map_exceptions()
    @transaction.atomic
    @validate_body(WorkspaceSerializer)
    def post(self, request, data):
        """Creates a new workspace for a user."""

        workspace_user = action_type_registry.get_by_type(CreateWorkspaceActionType).do(
            request.user, data["name"]
        )
        return Response(WorkspaceUserWorkspaceSerializer(workspace_user).data)


class WorkspaceView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the workspace related to the provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Workspaces"],
        operation_id="update_workspace",
        description=(
            "Updates the existing workspace related to the provided `workspace_id` parameter "
            "if the authorized user belongs to the workspace. It is not yet possible to "
            "add additional users to a workspace."
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
    def patch(self, request, data, workspace_id):
        """Updates the workspace if it belongs to a user."""

        workspace = CoreHandler().get_workspace_for_update(workspace_id)
        action_type_registry.get_by_type(UpdateWorkspaceActionType).do(
            request.user, workspace, data["name"]
        )
        return Response(WorkspaceSerializer(workspace).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Deletes the workspace related to the provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Workspaces"],
        operation_id="delete_workspace",
        description=(
            "Deletes an existing workspace if the authorized user belongs to the workspace. "
            "All the applications, databases, tables etc that were in the workspace are "
            "going to be deleted also."
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
    def delete(self, request, workspace_id: int):
        """Deletes an existing workspace if it belongs to a user."""

        locked_workspace = CoreHandler().get_workspace_for_update(workspace_id)
        action_type_registry.get_by_type(DeleteWorkspaceActionType).do(
            request.user, locked_workspace
        )
        return Response(status=204)


class WorkspaceLeaveView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Leaves the workspace related to the value.",
            )
        ],
        tags=["Workspaces"],
        operation_id="leave_workspace",
        description=(
            "Makes the authenticated user leave the workspace related to the provided "
            "`workspace_id` if the user is in that workspace. If the user is the last admin "
            "in the workspace, they will not be able to leave it. There must always be one "
            "admin in the workspace, otherwise it will be left without control. If that "
            "is the case, they must either delete the workspace or give another member admin "
            "permissions first."
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
    @transaction.atomic
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            WorkspaceUserIsLastAdmin: ERROR_GROUP_USER_IS_LAST_ADMIN,
        }
    )
    def post(self, request, workspace_id):
        """Leaves the workspace if the user is a member of it."""

        workspace = CoreHandler().get_workspace(workspace_id)
        action_type_registry.get(LeaveWorkspaceActionType.type).do(
            request.user, workspace
        )

        return Response(status=204)


class WorkspaceOrderView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Workspaces"],
        operation_id="order_workspaces",
        description=(
            "Changes the order of the provided workspace ids to the matching position that "
            "the id has in the list. If the authorized user does not belong to the "
            "workspace it will be ignored. The order will be custom for each user."
        ),
        request=OrderWorkspacesSerializer,
        responses={
            204: None,
        },
    )
    @validate_body(OrderWorkspacesSerializer)
    @transaction.atomic
    def post(self, request, data):
        """Updates to order of some workspaces for a user."""

        action_type_registry.get_by_type(OrderWorkspacesActionType).do(
            request.user, data["workspaces"]
        )
        return Response(status=204)


class WorkspacePermissionsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The workspace id we want the permission object for.",
            ),
        ],
        tags=["Workspaces"],
        operation_id="workspace_permissions",
        description=(
            "Returns a the permission data necessary to determine the permissions "
            "of a specific user over a specific workspace. \n"
            "See `core.handler.CoreHandler.get_permissions()` for more details."
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
    def get(self, request, workspace_id):
        """
        Returns the permission object for the given workspace.
        """

        workspace = CoreHandler().get_workspace(workspace_id)

        permissions = CoreHandler().get_permissions(request.user, workspace=workspace)

        return Response(permissions)

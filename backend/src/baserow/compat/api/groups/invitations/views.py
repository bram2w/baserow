from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from itsdangerous import BadSignature

from baserow.api.decorators import (
    map_exceptions,
    validate_body,
    validate_query_parameters,
)
from baserow.api.errors import (
    BAD_TOKEN_SIGNATURE,
    ERROR_GROUP_DOES_NOT_EXIST,
    ERROR_HOSTNAME_IS_NOT_ALLOWED,
    ERROR_USER_INVALID_GROUP_PERMISSIONS,
    ERROR_USER_NOT_IN_GROUP,
)
from baserow.api.schemas import get_error_schema
from baserow.api.workspaces.invitations.errors import (
    ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
    ERROR_GROUP_INVITATION_EMAIL_MISMATCH,
)
from baserow.api.workspaces.invitations.serializers import (
    CreateWorkspaceInvitationSerializer,
    GetWorkspaceInvitationsViewQuerySerializer,
    UpdateWorkspaceInvitationSerializer,
    UserWorkspaceInvitationSerializer,
    WorkspaceInvitationSerializer,
)
from baserow.api.workspaces.invitations.views import (
    AcceptWorkspaceInvitationView,
    RejectWorkspaceInvitationView,
    WorkspaceInvitationByTokenView,
    WorkspaceInvitationsView,
    WorkspaceInvitationView,
)
from baserow.api.workspaces.users.errors import ERROR_GROUP_USER_ALREADY_EXISTS
from baserow.api.workspaces.users.serializers import WorkspaceUserWorkspaceSerializer
from baserow.compat.api.conf import (
    INVITATION_DEPRECATION_PREFIXES as DEPRECATION_PREFIXES,
)
from baserow.core.exceptions import (
    BaseURLHostnameNotAllowed,
    UserInvalidWorkspacePermissionsError,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
    WorkspaceInvitationDoesNotExist,
    WorkspaceInvitationEmailMismatch,
    WorkspaceUserAlreadyExists,
)


class GroupInvitationsCompatView(WorkspaceInvitationsView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only invitations that are in the group related "
                "to the provided value.",
            )
        ],
        tags=["Group invitations"],
        deprecated=True,
        operation_id="list_group_invitations",
        description=(
            f"{DEPRECATION_PREFIXES['list_group_invitations']} Lists all the group "
            "invitations of the group related to the provided `group_id` parameter if "
            "the authorized user has admin rights to that group."
        ),
        responses={
            200: WorkspaceInvitationSerializer(many=True),
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_USER_INVALID_GROUP_PERMISSIONS"]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserInvalidWorkspacePermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    @validate_query_parameters(GetWorkspaceInvitationsViewQuerySerializer)
    def get(self, request, group_id, query_params):
        """Lists all the invitations of the provided group id."""

        return super().get(request, workspace_id=group_id)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Creates a group invitation to the group related to the "
                "provided value.",
            )
        ],
        tags=["Group invitations"],
        deprecated=True,
        operation_id="create_group_invitation",
        description=(
            f"{DEPRECATION_PREFIXES['create_group_invitation']} Creates a new group "
            "invitations for an email address if the authorized user has admin rights "
            "to the related group. An email containing a sign up link will be send "
            "to the user."
        ),
        request=CreateWorkspaceInvitationSerializer,
        responses={
            200: WorkspaceInvitationSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(CreateWorkspaceInvitationSerializer)
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserInvalidWorkspacePermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
            WorkspaceUserAlreadyExists: ERROR_GROUP_USER_ALREADY_EXISTS,
            BaseURLHostnameNotAllowed: ERROR_HOSTNAME_IS_NOT_ALLOWED,
        }
    )
    def post(self, request, data, group_id):
        """Creates a new group invitation and sends it the provided email."""

        return super().post(request, workspace_id=group_id)


class GroupInvitationCompatView(WorkspaceInvitationView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_invitation_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the group invitation related to the provided "
                "value.",
            )
        ],
        tags=["Group invitations"],
        deprecated=True,
        operation_id="get_group_invitation",
        description=(
            f"{DEPRECATION_PREFIXES['get_group_invitation']} Returns the requested "
            "group invitation if the authorized user has admin right to the "
            "related group"
        ),
        responses={
            200: WorkspaceInvitationSerializer,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_USER_INVALID_GROUP_PERMISSIONS"]
            ),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            WorkspaceInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserInvalidWorkspacePermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def get(self, request, group_invitation_id):
        """
        Selects a single group invitation and responds with a serialized version.
        """

        return super().get(request, group_invitation_id)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_invitation_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the group invitation related to the provided "
                "value.",
            )
        ],
        tags=["Group invitations"],
        deprecated=True,
        operation_id="update_group_invitation",
        description=(
            f"{DEPRECATION_PREFIXES['update_group_invitation']} Updates the existing "
            "group invitation related to the provided `group_invitation_id` "
            "param if the authorized user has admin rights to the related group."
        ),
        request=UpdateWorkspaceInvitationSerializer,
        responses={
            200: WorkspaceInvitationSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(UpdateWorkspaceInvitationSerializer)
    @map_exceptions(
        {
            WorkspaceInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserInvalidWorkspacePermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def patch(self, request, data, group_invitation_id):
        """Updates the group invitation if the user belongs to the group."""

        return super().patch(request, workspace_invitation_id=group_invitation_id)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_invitation_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Deletes the group invitation related to the provided "
                "value.",
            )
        ],
        tags=["Group invitations"],
        deprecated=True,
        operation_id="delete_group_invitation",
        description=(
            f"{DEPRECATION_PREFIXES['delete_group_invitation']} Deletes a group "
            "invitation if the authorized user has admin rights to the related group."
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
            WorkspaceInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserInvalidWorkspacePermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def delete(self, request, group_invitation_id):
        """
        Deletes an existing group_invitation if the user belongs to the group.
        """

        return super().delete(request, group_invitation_id)


class AcceptGroupInvitationCompatView(AcceptWorkspaceInvitationView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_invitation_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Accepts the group invitation related to the provided "
                "value.",
            )
        ],
        tags=["Group invitations"],
        deprecated=True,
        operation_id="accept_group_invitation",
        description=(
            f"{DEPRECATION_PREFIXES['accept_group_invitation']} Accepts a group "
            "invitation with the given id if the email address of the user matches "
            "that of the invitation."
        ),
        request=None,
        responses={
            200: WorkspaceUserWorkspaceSerializer,
            400: get_error_schema(["ERROR_GROUP_INVITATION_EMAIL_MISMATCH"]),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            WorkspaceInvitationEmailMismatch: ERROR_GROUP_INVITATION_EMAIL_MISMATCH,
            WorkspaceInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
        }
    )
    def post(self, request, group_invitation_id):
        """Accepts a group invitation."""

        return super().post(request, group_invitation_id)


class RejectGroupInvitationCompatView(RejectWorkspaceInvitationView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_invitation_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Rejects the group invitation related to the provided "
                "value.",
            )
        ],
        tags=["Group invitations"],
        deprecated=True,
        operation_id="reject_group_invitation",
        description=(
            f"{DEPRECATION_PREFIXES['reject_group_invitation']} Rejects a group "
            "invitation with the given id if the email address of the user matches "
            "that of the invitation."
        ),
        request=None,
        responses={
            204: None,
            400: get_error_schema(["ERROR_GROUP_INVITATION_EMAIL_MISMATCH"]),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            WorkspaceInvitationEmailMismatch: ERROR_GROUP_INVITATION_EMAIL_MISMATCH,
            WorkspaceInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
        }
    )
    def post(self, request, group_invitation_id):
        """Rejects a group invitation."""

        return super().post(request, group_invitation_id)


class GroupInvitationByTokenCompatView(WorkspaceInvitationByTokenView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                description="Returns the group invitation related to the provided "
                "token.",
            )
        ],
        tags=["Group invitations"],
        deprecated=True,
        operation_id="get_group_invitation_by_token",
        description=(
            f"{DEPRECATION_PREFIXES['get_group_invitation_by_token']} Responds with "
            "the serialized group invitation if an invitation with the provided token "
            "is found."
        ),
        responses={
            200: UserWorkspaceInvitationSerializer,
            400: get_error_schema(["BAD_TOKEN_SIGNATURE"]),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            BadSignature: BAD_TOKEN_SIGNATURE,
            WorkspaceInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, token):
        """
        Responds with the serialized group invitation if an invitation with the
        provided token is found.
        """

        return super().get(request, token)

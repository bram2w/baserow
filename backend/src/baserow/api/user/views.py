from typing import List

from django.conf import settings
from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from itsdangerous.exc import BadSignature, BadTimeSignature, SignatureExpired
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from baserow.api.actions.serializers import (
    UndoRedoResponseSerializer,
    get_undo_request_serializer,
)
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import (
    BAD_TOKEN_SIGNATURE,
    ERROR_HOSTNAME_IS_NOT_ALLOWED,
    EXPIRED_TOKEN_SIGNATURE,
)
from baserow.api.groups.invitations.errors import (
    ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
    ERROR_GROUP_INVITATION_EMAIL_MISMATCH,
)
from baserow.api.schemas import get_error_schema
from baserow.api.sessions import get_untrusted_client_session_id
from baserow.api.user.registries import user_data_registry
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import ActionScopeStr
from baserow.core.exceptions import (
    BaseURLHostnameNotAllowed,
    GroupInvitationDoesNotExist,
    GroupInvitationEmailMismatch,
    LockConflict,
)
from baserow.core.models import GroupInvitation, Template
from baserow.core.user.exceptions import (
    DeactivatedUserException,
    DisabledSignupError,
    InvalidPassword,
    ResetPasswordDisabledError,
    UserAlreadyExist,
    UserIsLastAdmin,
    UserNotFound,
)
from baserow.core.user.handler import UserHandler
from baserow.core.user.utils import generate_session_tokens_for_user

from .errors import (
    ERROR_ALREADY_EXISTS,
    ERROR_CLIENT_SESSION_ID_HEADER_NOT_SET,
    ERROR_DEACTIVATED_USER,
    ERROR_DISABLED_RESET_PASSWORD,
    ERROR_DISABLED_SIGNUP,
    ERROR_INVALID_CREDENTIALS,
    ERROR_INVALID_OLD_PASSWORD,
    ERROR_INVALID_REFRESH_TOKEN,
    ERROR_UNDO_REDO_LOCK_CONFLICT,
    ERROR_USER_IS_LAST_ADMIN,
    ERROR_USER_NOT_FOUND,
)
from .exceptions import ClientSessionIdHeaderNotSetException
from .schemas import (
    authenticate_user_schema,
    create_user_response_schema,
    verify_user_schema,
)
from .serializers import (
    AccountSerializer,
    ChangePasswordBodyValidationSerializer,
    DashboardSerializer,
    RegisterSerializer,
    ResetPasswordBodyValidationSerializer,
    SendResetPasswordEmailBodyValidationSerializer,
    TokenObtainPairWithUserSerializer,
    TokenRefreshWithUserSerializer,
    TokenVerifyWithUserSerializer,
    UserSerializer,
)

UndoRedoRequestSerializer = get_undo_request_serializer()


class ObtainJSONWebToken(TokenObtainPairView):
    """
    A slightly modified version of the ObtainJSONWebToken that uses an email as
    username and normalizes that email address using the normalize_email_address
    utility function.
    """

    serializer_class = TokenObtainPairWithUserSerializer

    @extend_schema(
        tags=["User"],
        operation_id="token_auth",
        description=(
            "Authenticates an existing user based on their email and their password. "
            "If successful, an access token and a refresh token will be returned."
        ),
        responses={
            200: create_user_response_schema,
            401: {
                "description": "An active user with the provided email and password "
                "could not be found."
            },
        },
        auth=[],
    )
    @map_exceptions(
        {
            AuthenticationFailed: ERROR_INVALID_CREDENTIALS,
            DeactivatedUserException: ERROR_DEACTIVATED_USER,
        }
    )
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)


class RefreshJSONWebToken(TokenRefreshView):
    serializer_class = TokenRefreshWithUserSerializer

    @extend_schema(
        tags=["User"],
        operation_id="token_refresh",
        description=(
            "Generate a new access_token that can be used to continue operating on Baserow "
            "starting from a valid refresh token."
        ),
        responses={
            200: authenticate_user_schema,
            401: {"description": "The JWT refresh token is invalid or expired."},
        },
        auth=[],
    )
    @map_exceptions({InvalidToken: ERROR_INVALID_REFRESH_TOKEN})
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)


class VerifyJSONWebToken(TokenVerifyView):
    serializer_class = TokenVerifyWithUserSerializer

    @extend_schema(
        tags=["User"],
        operation_id="token_verify",
        description=(
            "Verifies if the refresh token is valid and can be used "
            "to generate a new access_token."
        ),
        responses={
            200: verify_user_schema,
            401: {"description": "The JWT refresh token is invalid or expired."},
        },
        auth=[],
    )
    @map_exceptions({InvalidToken: ERROR_INVALID_REFRESH_TOKEN})
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)


class UserView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["User"],
        request=RegisterSerializer,
        operation_id="create_user",
        description=(
            "Creates a new user based on the provided values. If desired an "
            "authentication JWT can be generated right away. After creating an "
            "account the initial group containing a database is created."
        ),
        responses={
            200: create_user_response_schema,
            400: get_error_schema(
                [
                    "ERROR_ALREADY_EXISTS",
                    "ERROR_GROUP_INVITATION_DOES_NOT_EXIST",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "BAD_TOKEN_SIGNATURE",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
        auth=[],
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserAlreadyExist: ERROR_ALREADY_EXISTS,
            DeactivatedUserException: ERROR_DEACTIVATED_USER,
            BadSignature: BAD_TOKEN_SIGNATURE,
            GroupInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
            GroupInvitationEmailMismatch: ERROR_GROUP_INVITATION_EMAIL_MISMATCH,
            DisabledSignupError: ERROR_DISABLED_SIGNUP,
        }
    )
    @validate_body(RegisterSerializer)
    def post(self, request, data):
        """Registers a new user."""

        template = (
            Template.objects.get(pk=data["template_id"])
            if data["template_id"]
            else None
        )

        user = UserHandler().create_user(
            name=data["name"],
            email=data["email"],
            password=data["password"],
            language=data["language"],
            group_invitation_token=data.get("group_invitation_token"),
            template=template,
        )

        response = {"user": UserSerializer(user).data}

        if data["authenticate"]:
            response.update(
                {
                    **generate_session_tokens_for_user(
                        user, include_refresh_token=True
                    ),
                    **user_data_registry.get_all_user_data(user, request),
                }
            )

        return Response(response)


class SendResetPasswordEmailView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["User"],
        request=SendResetPasswordEmailBodyValidationSerializer,
        operation_id="send_password_reset_email",
        description=(
            "Sends an email containing the password reset link to the email address "
            "of the user. This will only be done if a user is found with the given "
            "email address. The endpoint will not fail if the email address is not "
            "found. The link is going to the valid for {valid} hours.".format(
                valid=int(settings.RESET_PASSWORD_TOKEN_MAX_AGE / 60 / 60)
            )
        ),
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_REQUEST_BODY_VALIDATION", "ERROR_HOSTNAME_IS_NOT_ALLOWED"]
            ),
        },
        auth=[],
    )
    @transaction.atomic
    @validate_body(SendResetPasswordEmailBodyValidationSerializer)
    @map_exceptions(
        {
            BaseURLHostnameNotAllowed: ERROR_HOSTNAME_IS_NOT_ALLOWED,
            ResetPasswordDisabledError: ERROR_DISABLED_RESET_PASSWORD,
        }
    )
    def post(self, request, data):
        """
        If the email is found, an email containing the password reset link is send to
        the user.
        """

        handler = UserHandler()

        try:
            user = handler.get_active_user(email=data["email"])
            handler.send_reset_password_email(user, data["base_url"])
        except UserNotFound:
            pass

        return Response("", status=204)


class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["User"],
        request=ResetPasswordBodyValidationSerializer,
        operation_id="reset_password",
        description=(
            "Changes the password of a user if the reset token is valid. The "
            "**send_password_reset_email** endpoint sends an email to the user "
            "containing the token. That token can be used to change the password "
            "here without providing the old password."
        ),
        responses={
            204: None,
            400: get_error_schema(
                [
                    "BAD_TOKEN_SIGNATURE",
                    "EXPIRED_TOKEN_SIGNATURE",
                    "ERROR_USER_NOT_FOUND",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
        },
        auth=[],
    )
    @transaction.atomic
    @map_exceptions(
        {
            BadSignature: BAD_TOKEN_SIGNATURE,
            BadTimeSignature: BAD_TOKEN_SIGNATURE,
            SignatureExpired: EXPIRED_TOKEN_SIGNATURE,
            UserNotFound: ERROR_USER_NOT_FOUND,
            ResetPasswordDisabledError: ERROR_DISABLED_RESET_PASSWORD,
        }
    )
    @validate_body(ResetPasswordBodyValidationSerializer)
    def post(self, request, data):
        """Changes users password if the provided reset token is valid."""

        handler = UserHandler()
        handler.reset_password(data["token"], data["password"])

        return Response("", status=204)


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["User"],
        request=ChangePasswordBodyValidationSerializer,
        operation_id="change_password",
        description=(
            "Changes the password of an authenticated user, but only if the old "
            "password matches."
        ),
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_INVALID_OLD_PASSWORD",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            InvalidPassword: ERROR_INVALID_OLD_PASSWORD,
        }
    )
    @validate_body(ChangePasswordBodyValidationSerializer)
    def post(self, request, data):
        """Changes the authenticated user's password if the old password is correct."""

        handler = UserHandler()
        handler.change_password(
            request.user, data["old_password"], data["new_password"]
        )

        return Response("", status=204)


class AccountView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["User"],
        request=AccountSerializer,
        operation_id="update_account",
        description="Updates the account information of the authenticated user.",
        responses={
            200: AccountSerializer,
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
        },
    )
    @transaction.atomic
    @validate_body(AccountSerializer)
    def patch(self, request, data):
        """Updates editable user account information."""

        user = UserHandler().update_user(
            request.user,
            **data,
        )
        return Response(AccountSerializer(user).data)


class ScheduleAccountDeletionView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["User"],
        operation_id="schedule_account_deletion",
        description=(
            "Schedules the account deletion of the authenticated user. "
            "The user will be permanently deleted after the grace delay defined "
            "by the instance administrator."
        ),
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserIsLastAdmin: ERROR_USER_IS_LAST_ADMIN,
        }
    )
    def post(self, request):
        """Schedules user account deletion."""

        UserHandler().schedule_user_deletion(request.user)
        return Response(status=204)


class DashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["User"],
        operation_id="dashboard",
        description=(
            "Lists all the relevant user information that for example could be shown "
            "on a dashboard. It will contain all the pending group invitations for "
            "that user."
        ),
        responses={200: DashboardSerializer},
    )
    @transaction.atomic
    def get(self, request):
        """Lists all the data related to the user dashboard page."""

        group_invitations = GroupInvitation.objects.select_related(
            "group", "invited_by"
        ).filter(email=request.user.username)
        dashboard_serializer = DashboardSerializer(
            {"group_invitations": group_invitations}
        )
        return Response(dashboard_serializer.data)


UNDO_REDO_EXCEPTIONS_MAP = {
    ClientSessionIdHeaderNotSetException: ERROR_CLIENT_SESSION_ID_HEADER_NOT_SET,
    LockConflict: ERROR_UNDO_REDO_LOCK_CONFLICT,
}


class UndoView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name=settings.CLIENT_SESSION_ID_HEADER,
                location=OpenApiParameter.HEADER,
                type=OpenApiTypes.UUID,
                required=True,
                description="The particular client session to undo actions for. The "
                "actions must have been performed with this same header set with the "
                "same value for them to be undoable by this endpoint.",
            )
        ],
        tags=["User"],
        request=UndoRedoRequestSerializer,
        operation_id="undo",
        description=(
            "undoes the latest undoable action performed by the user making the "
            f"request. a {settings.CLIENT_SESSION_ID_HEADER} header must be provided "
            f"and only actions which were performed the same user with the same "
            f"{settings.CLIENT_SESSION_ID_HEADER} value set on the api request that "
            f"performed the action will be undone."
            f"Additionally the {settings.CLIENT_SESSION_ID_HEADER} header must "
            f"be between 1 and {settings.MAX_CLIENT_SESSION_ID_LENGTH} characters long "
            f"and must only contain alphanumeric or the - characters."
        ),
        responses={200: UndoRedoResponseSerializer},
    )
    @validate_body(UndoRedoRequestSerializer)
    @map_exceptions(UNDO_REDO_EXCEPTIONS_MAP)
    @transaction.atomic
    def patch(self, request, data: List[ActionScopeStr]):
        session_id = get_untrusted_client_session_id(request.user)
        if session_id is None:
            raise ClientSessionIdHeaderNotSetException()
        undone_actions = ActionHandler.undo(request.user, data, session_id)
        serializer = UndoRedoResponseSerializer({"actions": undone_actions})
        return Response(serializer.data, status=200)


class RedoView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name=settings.CLIENT_SESSION_ID_HEADER,
                location=OpenApiParameter.HEADER,
                type=OpenApiTypes.UUID,
                required=True,
                description="The particular client session to redo actions for. The "
                "actions must have been performed with this same header set with the "
                "same value for them to be redoable by this endpoint.",
            )
        ],
        tags=["User"],
        request=UndoRedoRequestSerializer,
        operation_id="redo",
        description=(
            "Redoes the latest redoable action performed by the user making the "
            f"request. a {settings.CLIENT_SESSION_ID_HEADER} header must be provided "
            f"and only actions which were performed the same user with the same "
            f"{settings.CLIENT_SESSION_ID_HEADER} value set on the api request that "
            f"performed the action will be redone."
            f"Additionally the {settings.CLIENT_SESSION_ID_HEADER} header must "
            f"be between 1 and {settings.MAX_CLIENT_SESSION_ID_LENGTH} characters long "
            f"and must only contain alphanumeric or the - characters."
        ),
        responses={200: UndoRedoResponseSerializer},
    )
    @validate_body(UndoRedoRequestSerializer)
    @map_exceptions(UNDO_REDO_EXCEPTIONS_MAP)
    @transaction.atomic
    def patch(self, request, data: List[ActionScopeStr]):
        session_id = get_untrusted_client_session_id(request.user)
        if session_id is None:
            raise ClientSessionIdHeaderNotSetException()
        redone_actions = ActionHandler.redo(request.user, data, session_id)
        serializer = UndoRedoResponseSerializer({"actions": redone_actions})
        return Response(serializer.data, status=200)

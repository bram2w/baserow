from django.db import transaction
from itsdangerous.exc import BadSignature, BadTimeSignature, SignatureExpired

from django.conf import settings

from drf_spectacular.utils import extend_schema

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import (
    ObtainJSONWebTokenView as RegularObtainJSONWebToken,
    RefreshJSONWebTokenView as RegularRefreshJSONWebToken,
    VerifyJSONWebTokenView as RegularVerifyJSONWebToken,
)

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import (
    BAD_TOKEN_SIGNATURE,
    EXPIRED_TOKEN_SIGNATURE,
    ERROR_HOSTNAME_IS_NOT_ALLOWED,
)
from baserow.api.groups.invitations.errors import (
    ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
    ERROR_GROUP_INVITATION_EMAIL_MISMATCH,
)
from baserow.api.schemas import get_error_schema
from baserow.core.exceptions import (
    BaseURLHostnameNotAllowed,
    GroupInvitationEmailMismatch,
    GroupInvitationDoesNotExist,
)
from baserow.core.models import GroupInvitation, Template
from baserow.core.user.handler import UserHandler
from baserow.core.user.exceptions import (
    UserAlreadyExist,
    UserNotFound,
    InvalidPassword,
    DisabledSignupError,
)

from .serializers import (
    AccountSerializer,
    RegisterSerializer,
    UserSerializer,
    SendResetPasswordEmailBodyValidationSerializer,
    ResetPasswordBodyValidationSerializer,
    ChangePasswordBodyValidationSerializer,
    NormalizedEmailWebTokenSerializer,
    DashboardSerializer,
)
from .errors import (
    ERROR_ALREADY_EXISTS,
    ERROR_USER_NOT_FOUND,
    ERROR_INVALID_OLD_PASSWORD,
    ERROR_DISABLED_SIGNUP,
)
from .schemas import create_user_response_schema, authenticate_user_schema


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class ObtainJSONWebToken(RegularObtainJSONWebToken):
    """
    A slightly modified version of the ObtainJSONWebToken that uses an email as
    username and normalizes that email address using the normalize_email_address
    utility function.
    """

    serializer_class = NormalizedEmailWebTokenSerializer

    @extend_schema(
        tags=["User"],
        operation_id="token_auth",
        description=(
            "Authenticates an existing user based on their username, which is their "
            "email address, and their password. If successful a JWT token will be "
            "generated that can be used to authorize for other endpoints that require "
            "authorization. The token will be valid for {valid} minutes, so it has to "
            "be refreshed using the **token_refresh** endpoint before that "
            "time.".format(
                valid=int(settings.JWT_AUTH["JWT_EXPIRATION_DELTA"].seconds / 60)
            )
        ),
        responses={
            200: authenticate_user_schema,
            400: {
                "description": "A user with the provided username and password is "
                "not found."
            },
        },
        auth=[None],
    )
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)


class RefreshJSONWebToken(RegularRefreshJSONWebToken):
    @extend_schema(
        tags=["User"],
        operation_id="token_refresh",
        description=(
            "Refreshes an existing JWT token. If the the token is valid, a new "
            "token will be included in the response. It will be valid for {valid} "
            "minutes.".format(
                valid=int(settings.JWT_AUTH["JWT_EXPIRATION_DELTA"].seconds / 60)
            )
        ),
        responses={
            200: authenticate_user_schema,
            400: {"description": "The token is invalid or expired."},
        },
        auth=[None],
    )
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)


class VerifyJSONWebToken(RegularVerifyJSONWebToken):
    @extend_schema(
        tags=["User"],
        operation_id="token_verify",
        description="Verifies if the token is still valid.",
        responses={
            200: authenticate_user_schema,
            400: {"description": "The token is invalid or expired."},
        },
        auth=[None],
    )
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
            "authentication token can be generated right away. After creating an "
            "account the initial group containing a database is created."
        ),
        responses={
            200: create_user_response_schema,
            400: get_error_schema(
                [
                    "ERROR_ALREADY_EXISTS",
                    "ERROR_GROUP_INVITATION_DOES_NOT_EXIST"
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "BAD_TOKEN_SIGNATURE",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
        auth=[None],
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserAlreadyExist: ERROR_ALREADY_EXISTS,
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
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            response.update(token=token)

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
        auth=[None],
    )
    @transaction.atomic
    @validate_body(SendResetPasswordEmailBodyValidationSerializer)
    @map_exceptions({BaseURLHostnameNotAllowed: ERROR_HOSTNAME_IS_NOT_ALLOWED})
    def post(self, request, data):
        """
        If the email is found, an email containing the password reset link is send to
        the user.
        """

        handler = UserHandler()

        try:
            user = handler.get_user(email=data["email"])
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
        auth=[None],
    )
    @transaction.atomic
    @map_exceptions(
        {
            BadSignature: BAD_TOKEN_SIGNATURE,
            BadTimeSignature: BAD_TOKEN_SIGNATURE,
            SignatureExpired: EXPIRED_TOKEN_SIGNATURE,
            UserNotFound: ERROR_USER_NOT_FOUND,
        }
    )
    @validate_body(ResetPasswordBodyValidationSerializer)
    def post(self, request, data):
        """Changes users password if the provided token is valid."""

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
        operation_id="get_account",
        description=(
            "Responds with account information of the authenticated user. "
            "For example the chosen `language` and `name` are included "
            "in the response."
        ),
        responses={
            200: AccountSerializer,
        },
    )
    @transaction.atomic
    def get(self, request):
        """Returns user account."""

        account_serializer = AccountSerializer(request.user)
        return Response(account_serializer.data)

    @extend_schema(
        tags=["User"],
        request=AccountSerializer,
        operation_id="update_account",
        description=("Updates the account information of the authenticated user."),
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
        """Update editable user account information."""

        user = UserHandler().update_user(
            request.user,
            **data,
        )
        return Response(AccountSerializer(user).data)


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

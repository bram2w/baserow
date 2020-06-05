from django.db import transaction
from itsdangerous.exc import BadSignature, SignatureExpired

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import ObtainJSONWebToken as RegularObtainJSONWebToken

from baserow.api.v0.decorators import map_exceptions, validate_body
from baserow.api.v0.errors import BAD_TOKEN_SIGNATURE, EXPIRED_TOKEN_SIGNATURE
from baserow.core.user.handler import UserHandler
from baserow.core.user.exceptions import (
    UserAlreadyExist, UserNotFound, InvalidPassword
)

from .serializers import (
    RegisterSerializer, UserSerializer, SendResetPasswordEmailBodyValidationSerializer,
    ResetPasswordBodyValidationSerializer, ChangePasswordBodyValidationSerializer,
    NormalizedEmailWebTokenSerializer,
)
from .errors import (
    ERROR_ALREADY_EXISTS, ERROR_USER_NOT_FOUND, ERROR_INVALID_OLD_PASSWORD
)


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class ObtainJSONWebToken(RegularObtainJSONWebToken):
    """
    A slightly modified version of the ObtainJSONWebToken that uses an email as
    username and normalizes that email address using the normalize_email_address
    utility function.
    """

    serializer_class = NormalizedEmailWebTokenSerializer


class UserView(APIView):
    permission_classes = (AllowAny,)

    @transaction.atomic
    @map_exceptions({
        UserAlreadyExist: ERROR_ALREADY_EXISTS
    })
    @validate_body(RegisterSerializer)
    def post(self, request, data):
        """Registers a new user."""

        user = UserHandler().create_user(name=data['name'], email=data['email'],
                                         password=data['password'])

        response = {'user': UserSerializer(user).data}

        if data['authenticate']:
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            response.update(token=token)

        return Response(response)


class SendResetPasswordEmailView(APIView):
    permission_classes = (AllowAny,)

    @transaction.atomic
    @validate_body(SendResetPasswordEmailBodyValidationSerializer)
    def post(self, request, data):
        """
        If the email is found, an email containing the password reset link is send to
        the user.
        """

        handler = UserHandler()

        try:
            user = handler.get_user(email=data['email'])
            handler.send_reset_password_email(user, data['base_url'])
        except UserNotFound:
            pass

        return Response('', status=204)


class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)

    @transaction.atomic
    @map_exceptions({
        BadSignature: BAD_TOKEN_SIGNATURE,
        SignatureExpired: EXPIRED_TOKEN_SIGNATURE,
        UserNotFound: ERROR_USER_NOT_FOUND
    })
    @validate_body(ResetPasswordBodyValidationSerializer)
    def post(self, request, data):
        """Changes users password if the provided token is valid."""

        handler = UserHandler()
        handler.reset_password(data['token'], data['password'])

        return Response('', status=204)


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    @map_exceptions({
        InvalidPassword: ERROR_INVALID_OLD_PASSWORD,
    })
    @validate_body(ChangePasswordBodyValidationSerializer)
    def post(self, request, data):
        """Changes the authenticated user's password if the old password is correct."""

        handler = UserHandler()
        handler.change_password(request.user, data['old_password'],
                                data['new_password'])

        return Response('', status=204)

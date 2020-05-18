from django.db import transaction
from itsdangerous.exc import BadSignature, SignatureExpired

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_jwt.settings import api_settings

from baserow.api.v0.decorators import map_exceptions, validate_body
from baserow.api.v0.errors import BAD_TOKEN_SIGNATURE, EXPIRED_TOKEN_SIGNATURE
from baserow.core.user.handler import UserHandler
from baserow.core.user.exceptions import UserAlreadyExist, UserNotFound

from .serializers import (
    RegisterSerializer, UserSerializer, SendResetPasswordEmailBodyValidationSerializer,
    ResetPasswordBodyValidationSerializer
)
from .errors import ERROR_ALREADY_EXISTS, ERROR_USER_NOT_FOUND


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


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

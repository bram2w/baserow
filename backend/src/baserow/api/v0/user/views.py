from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_jwt.settings import api_settings

from baserow.api.v0.decorators import map_exceptions, validate_body
from baserow.user.handler import UserHandler
from baserow.user.exceptions import UserAlreadyExist

from .serializers import RegisterSerializer, UserSerializer
from .errors import ERROR_ALREADY_EXISTS


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

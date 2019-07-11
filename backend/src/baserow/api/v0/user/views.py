from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_jwt.settings import api_settings

from baserow.api.v0.decorators import map_exceptions
from baserow.user.handler import UserHandler
from baserow.user.exceptions import UserAlreadyExist


from .serializers import RegisterSerializer, UserSerializer


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class UserView(APIView):
    permission_classes = (AllowAny,)
    user_handler = UserHandler()

    @transaction.atomic
    @map_exceptions({
        UserAlreadyExist: 'ERROR_ALREADY_EXISTS'
    })
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.data
        user = self.user_handler.create_user(name=data['name'], email=data['email'],
                                             password=data['password'])

        response = {'user': UserSerializer(user).data}

        if data['authenticate']:
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            response.update(token=token)

        return Response(response)

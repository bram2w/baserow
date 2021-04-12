import jwt

from drf_spectacular.extensions import OpenApiAuthenticationExtension

from django.utils.translation import ugettext as _

from rest_framework import exceptions
from rest_framework_jwt.authentication import (
    jwt_decode_handler,
    JSONWebTokenAuthentication as JWTJSONWebTokenAuthentication,
)


class JSONWebTokenAuthentication(JWTJSONWebTokenAuthentication):
    def authenticate(self, request):
        """
        This method is basically a copy of
        rest_framework_jwt.authentication.BaseJSONWebTokenAuthentication.authenticate
        it only adds a machine readable error to the AuthenticationFailed response.
        """

        jwt_value = self.get_jwt_value(request)
        if jwt_value is None:
            return None

        try:
            payload = jwt_decode_handler(jwt_value)
        except jwt.ExpiredSignature:
            msg = _("Signature has expired.")
            raise exceptions.AuthenticationFailed(
                {"detail": msg, "error": "ERROR_SIGNATURE_HAS_EXPIRED"}
            )
        except jwt.DecodeError:
            msg = _("Error decoding signature.")
            raise exceptions.AuthenticationFailed(
                {"detail": msg, "error": "ERROR_DECODING_SIGNATURE"}
            )
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed()

        user = self.authenticate_credentials(payload)

        # @TODO this should actually somehow be moved to the ws app.
        user.web_socket_id = request.headers.get("WebSocketId")

        return user, jwt_value


class JSONWebTokenAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "baserow.api.authentication.JSONWebTokenAuthentication"
    name = "JWT"
    match_subclasses = True
    priority = -1

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT your_token",
        }

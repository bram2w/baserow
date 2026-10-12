from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.integrations.errors import ERROR_INTEGRATION_DOES_NOT_EXIST
from baserow.api.schemas import get_error_schema
from baserow.contrib.integrations.oauth2.exceptions import (
    OAuth2IntegrationNotConfigured,
    OAuth2InvalidReturnUrl,
    OAuth2InvalidState,
    OAuth2TokenRequestFailed,
)
from baserow.contrib.integrations.oauth2.handler import OAuth2IntegrationHandler
from baserow.contrib.integrations.oauth2.integration_types import (
    OAuth2IntegrationTypeMixin,
)
from baserow.core.exceptions import UserNotInWorkspace
from baserow.core.integrations.exceptions import IntegrationDoesNotExist
from baserow.core.integrations.handler import IntegrationHandler

from .errors import (
    ERROR_OAUTH2_INTEGRATION_NOT_CONFIGURED,
    ERROR_OAUTH2_INVALID_RETURN_URL,
    ERROR_OAUTH2_INVALID_STATE,
    ERROR_OAUTH2_NOT_SUPPORTED,
    ERROR_OAUTH2_TOKEN_REQUEST_FAILED,
)
from .serializers import (
    OAuth2AuthorizeRequestSerializer,
    OAuth2AuthorizeResponseSerializer,
    OAuth2CompleteRequestSerializer,
    OAuth2CompleteResponseSerializer,
    OAuth2RedirectUriResponseSerializer,
)


class OAuth2NotSupported(Exception):
    """The integration type has no OAuth2 flow."""


class OAuth2AuthorizeView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="integration_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The integration to connect to an account.",
            ),
        ],
        tags=["Integrations"],
        operation_id="oauth2_authorize_integration",
        description=(
            "Starts connecting an OAuth2 integration (Google, Microsoft) to an "
            "account. Answers the provider's consent URL to send the browser to; "
            "the provider later calls back to Baserow, which hands the code to "
            "the frontend to complete the connection and return to `return_url`."
        ),
        request=OAuth2AuthorizeRequestSerializer,
        responses={
            200: OAuth2AuthorizeResponseSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_OAUTH2_INTEGRATION_NOT_CONFIGURED",
                    "ERROR_OAUTH2_INVALID_RETURN_URL",
                    "ERROR_OAUTH2_NOT_SUPPORTED",
                ]
            ),
            404: get_error_schema(["ERROR_INTEGRATION_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            IntegrationDoesNotExist: ERROR_INTEGRATION_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            OAuth2IntegrationNotConfigured: ERROR_OAUTH2_INTEGRATION_NOT_CONFIGURED,
            OAuth2InvalidReturnUrl: ERROR_OAUTH2_INVALID_RETURN_URL,
            OAuth2NotSupported: ERROR_OAUTH2_NOT_SUPPORTED,
        }
    )
    @validate_body(OAuth2AuthorizeRequestSerializer, return_validated=True)
    def post(self, request, data, integration_id: int):
        integration = IntegrationHandler().get_integration(integration_id)
        if not isinstance(integration.get_type(), OAuth2IntegrationTypeMixin):
            raise OAuth2NotSupported()
        authorization_url = OAuth2IntegrationHandler().get_authorization_url(
            request.user, integration, data["return_url"]
        )
        return Response({"authorization_url": authorization_url})


# The frontend page that finishes the flow with the user's own session.
FRONTEND_COMPLETE_PATH = "/integration/oauth2/complete"
# Only what the frontend needs to finish or explain the outcome is forwarded.
FORWARDED_CALLBACK_PARAMS = ("code", "state", "error", "error_description")


class OAuth2CallbackView(APIView):
    # The provider's redirect carries no Baserow session, so nothing is
    # exchanged here: the browser is sent on to the frontend, which finishes
    # the flow as the logged in user. Kept on the backend so the redirect URI
    # registered with the provider does not change.
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="code",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="The authorization code the provider issued.",
            ),
            OpenApiParameter(
                name="state",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="The signed state Baserow put in the consent URL.",
            ),
            OpenApiParameter(
                name="error",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Set by the provider when consent was refused.",
            ),
        ],
        tags=["Integrations"],
        operation_id="oauth2_integration_callback",
        description=(
            "Where the provider sends the browser after the consent screen. "
            "Redirects to the frontend, which completes the connection with "
            "the `oauth2_complete_integration` endpoint."
        ),
        responses={302: None},
    )
    def get(self, request):
        params = {
            name: request.GET[name]
            for name in FORWARDED_CALLBACK_PARAMS
            if request.GET.get(name)
        }
        return HttpResponseRedirect(
            f"{settings.PUBLIC_WEB_FRONTEND_URL.rstrip('/')}{FRONTEND_COMPLETE_PATH}?"
            + urlencode(params)
        )


class OAuth2CompleteView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Integrations"],
        operation_id="oauth2_complete_integration",
        description=(
            "Finishes connecting an OAuth2 integration: trades the provider's "
            "code for tokens and stores them on the integration. Only the user "
            "who started the flow can complete it, and only once."
        ),
        request=OAuth2CompleteRequestSerializer,
        responses={
            200: OAuth2CompleteResponseSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_OAUTH2_INVALID_STATE",
                    "ERROR_OAUTH2_TOKEN_REQUEST_FAILED",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            OAuth2InvalidState: ERROR_OAUTH2_INVALID_STATE,
            OAuth2TokenRequestFailed: ERROR_OAUTH2_TOKEN_REQUEST_FAILED,
        }
    )
    @validate_body(OAuth2CompleteRequestSerializer, return_validated=True)
    def post(self, request, data):
        state = OAuth2IntegrationHandler().complete_authorization(
            request.user, data["code"], data["state"]
        )
        return Response(
            {
                "integration_id": state["integration_id"],
                "return_url": state["return_url"],
            }
        )


class OAuth2RedirectUriView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Integrations"],
        operation_id="oauth2_integration_redirect_uri",
        description=(
            "The redirect URI Baserow sends to OAuth2 providers, to register "
            "with the provider's app."
        ),
        responses={200: OAuth2RedirectUriResponseSerializer},
    )
    def get(self, request):
        return Response({"redirect_uri": OAuth2IntegrationHandler().get_redirect_uri()})

from typing import Any, Dict
from urllib.parse import urljoin

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_query_parameters
from baserow.api.schemas import get_error_schema
from baserow.core.user.exceptions import UserAlreadyExist
from baserow_enterprise.api.sso.saml.errors import ERROR_SAML_INVALID_LOGIN_REQUEST
from baserow_enterprise.api.sso.utils import (
    SsoErrorCode,
    get_saml_login_relative_url,
    redirect_to_sign_in_error_page,
    redirect_user_on_success,
)
from baserow_enterprise.auth_provider.exceptions import DifferentAuthProvider
from baserow_enterprise.sso.saml.exceptions import (
    InvalidSamlConfiguration,
    InvalidSamlRequest,
    InvalidSamlResponse,
)
from baserow_enterprise.sso.saml.handler import SamlAuthProviderHandler
from baserow_enterprise.sso.utils import (
    check_sso_feature_is_active_or_raise,
    is_sso_feature_active,
)

from .serializers import SamlLoginRequestSerializer


@method_decorator(csrf_exempt, name="dispatch")
class AssertionConsumerServiceView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        """
        This is the endpoint the SAML identity provider will call after the user
        has been authenticated there. If valid, the SAML response will contain
        the user's information needed to retrieve or create the user in the
        database. Once we have a valid user, a frontend url will be returned
        with the user's token as a query parameter so that the frontend can
        authenticate and start a new session for the user.
        """

        if not is_sso_feature_active():
            return redirect_to_sign_in_error_page(SsoErrorCode.FEATURE_NOT_ACTIVE)

        try:
            saml_response = request.POST.get("SAMLResponse")
            user = SamlAuthProviderHandler.sign_in_user_from_saml_response(
                saml_response
            )
        except (InvalidSamlResponse, InvalidSamlConfiguration):
            return redirect_to_sign_in_error_page(SsoErrorCode.INVALID_SAML_RESPONSE)
        except UserAlreadyExist:
            return redirect_to_sign_in_error_page(SsoErrorCode.ERROR_USER_DEACTIVATED)
        except DifferentAuthProvider:
            return redirect_to_sign_in_error_page(SsoErrorCode.DIFFERENT_PROVIDER)

        requested_url = request.POST["RelayState"]
        return redirect_user_on_success(user, requested_url)


@method_decorator(csrf_exempt, name="dispatch")
class BaserowInitiatedSingleSignOn(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        This is the endpoint that is called when the user wants to initiate the
        SSO SAML login from Baserow (the service provider). The user will be
        redirected to the SAML identity provider (IdP) where it's possible to insert
        the credentials. After the authentication, the user will be redirected back
        to the assertion consumer service endpoint (ACS) where the SAML response
        will be validated and a new JWT session token will be provided.
        """

        if not is_sso_feature_active():
            return redirect_to_sign_in_error_page(SsoErrorCode.FEATURE_NOT_ACTIVE)

        try:
            user_email = request.GET.get("email")
            requested_url = request.GET.get("original", "")
            idp_sign_in_url = SamlAuthProviderHandler.get_sign_in_url(
                user_email, requested_url
            )
        except (InvalidSamlConfiguration, InvalidSamlRequest):
            return redirect_to_sign_in_error_page(SsoErrorCode.INVALID_SAML_REQUEST)
        return redirect(idp_sign_in_url)


class AdminAuthProvidersLoginUrlView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="email",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="The email address of the user that want to sign in using SAML.",
            ),
            OpenApiParameter(
                name="original",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "The url to which the user should be redirected after a successful login."
                ),
            ),
        ],
        tags=["Auth"],
        request=SamlLoginRequestSerializer,
        operation_id="auth_provider_login_url",
        description=(
            "Return the correct redirect_url to initiate the SSO SAML login. "
            "It needs an email address if multiple SAML providers are configured, "
            "Otherwise it will return the redirect_url for the only configured "
            "SAML provider."
        ),
        responses={
            200: Dict[str, str],
            400: get_error_schema(["ERROR_SAML_INVALID_LOGIN_REQUEST"]),
        },
        auth=[],
    )
    @transaction.atomic
    @validate_query_parameters(SamlLoginRequestSerializer, return_validated=True)
    @map_exceptions(
        {
            InvalidSamlRequest: ERROR_SAML_INVALID_LOGIN_REQUEST,
        }
    )
    def get(self, request: Request, query_params: Dict[str, Any]) -> Response:
        """Return the correct link for the SP initiated SAML login."""

        check_sso_feature_is_active_or_raise()

        # check there is a valid SAML provider configured for the email provided
        SamlAuthProviderHandler.get_saml_auth_provider_from_email(
            query_params.get("email")
        )

        saml_login_relative_url = get_saml_login_relative_url(query_params)
        redirect_url = urljoin(settings.PUBLIC_BACKEND_URL, saml_login_relative_url)
        return Response({"redirect_url": redirect_url})

from django.db import transaction
from django.shortcuts import redirect

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from baserow.core.auth_provider.exceptions import AuthProviderModelNotFound
from baserow.core.registries import auth_provider_type_registry
from baserow.core.user.exceptions import UserAlreadyExist
from baserow_enterprise.api.sso.utils import (
    SsoErrorCode,
    redirect_to_sign_in_error_page,
    redirect_user_on_success,
)
from baserow_enterprise.auth_provider.exceptions import DifferentAuthProvider
from baserow_enterprise.auth_provider.handler import AuthProviderHandler
from baserow_enterprise.sso.exceptions import AuthFlowError
from baserow_enterprise.sso.utils import is_sso_feature_active


class OAuth2LoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="provider_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the provider for redirect.",
            ),
        ],
        tags=["Auth"],
        operation_id="oauth_provider_login_redirect",
        description=(
            "Redirects to the OAuth2 provider's authentication URL "
            "based on the provided auth provider's id."
        ),
        responses={
            302: None,
        },
        auth=[],
    )
    @transaction.atomic
    def get(self, request, provider_id):
        """
        Redirects users to the authorization URL of the chosen provider
        to start OAuth2 login flow.
        """

        if not is_sso_feature_active():
            return redirect_to_sign_in_error_page(SsoErrorCode.FEATURE_NOT_ACTIVE)

        try:
            provider = AuthProviderHandler.get_auth_provider(provider_id)
            provider_type = auth_provider_type_registry.get_by_model(provider)
        except AuthProviderModelNotFound:
            return redirect_to_sign_in_error_page(SsoErrorCode.PROVIDER_DOES_NOT_EXIST)

        redirect_url = provider_type.get_authorization_url(
            provider.specific_class.objects.get(id=provider_id)
        )

        return redirect(redirect_url)


class OAuth2CallbackView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="provider_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the provider for which to process the callback.",
            ),
            OpenApiParameter(
                name="code",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="The id of the provider for which to process the callback.",
            ),
        ],
        tags=["Auth"],
        operation_id="oauth_provider_login_callback",
        description=(
            "Processes callback from OAuth2 provider and "
            "logs the user in if successful."
        ),
        responses={
            302: None,
        },
        auth=[],
    )
    @transaction.atomic
    def get(self, request, provider_id):
        """
        Processes callback from OAuth2 authentication provider by
        using the 'code' parameter to obtain tokens and query for user
        details. If successful, the user is given JWT token and is logged
        in.
        """

        if not is_sso_feature_active():
            return redirect_to_sign_in_error_page(SsoErrorCode.FEATURE_NOT_ACTIVE)

        try:
            provider = AuthProviderHandler.get_auth_provider(provider_id)
            provider_type = auth_provider_type_registry.get_by_model(provider)
            code = request.query_params.get("code", None)
            userinfo = provider_type.get_user_info(provider, code)
            user = AuthProviderHandler.get_or_create_user_and_sign_in_via_auth_provider(
                userinfo, provider
            )
        except AuthProviderModelNotFound:
            return redirect_to_sign_in_error_page(SsoErrorCode.PROVIDER_DOES_NOT_EXIST)
        except AuthFlowError:
            return redirect_to_sign_in_error_page(SsoErrorCode.AUTH_FLOW_ERROR)
        except UserAlreadyExist:
            return redirect_to_sign_in_error_page(SsoErrorCode.ERROR_USER_DEACTIVATED)
        except DifferentAuthProvider:
            return redirect_to_sign_in_error_page(SsoErrorCode.DIFFERENT_PROVIDER)

        return redirect_user_on_success(user)

from typing import Any, Dict
from urllib.request import Request

from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.auth_provider.errors import (
    ERROR_AUTH_PROVIDER_CANNOT_BE_CREATED,
    ERROR_AUTH_PROVIDER_CANNOT_BE_DELETED,
    ERROR_AUTH_PROVIDER_DOES_NOT_EXIST,
    ERROR_CANNOT_DISABLE_ALL_AUTH_PROVIDERS,
)
from baserow.api.auth_provider.serializers import AuthProviderSerializer
from baserow.api.decorators import map_exceptions, validate_body_custom_fields
from baserow.api.schemas import get_error_schema
from baserow.api.utils import (
    DiscriminatorCustomFieldsMappingSerializer,
    validate_data_custom_fields,
)
from baserow.core.auth_provider.exceptions import (
    AuthProviderModelNotFound,
    CannotCreateAuthProvider,
    CannotDeleteAuthProvider,
    CannotDisableLastAuthProvider,
)
from baserow.core.auth_provider.handler import AuthProviderHandler
from baserow.core.auth_provider.models import AuthProviderModel
from baserow.core.registries import auth_provider_type_registry
from baserow_enterprise.sso.utils import check_sso_feature_is_active_or_raise

from .serializers import (
    CreateAuthProviderSerializer,
    NextAuthProviderIdSerializer,
    UpdateAuthProviderSerializer,
)


class AdminAuthProvidersView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Auth"],
        request=None,
        operation_id="create_auth_provider",
        description=(
            "Creates a new authentication provider. This can be used to enable "
            "authentication with a third party service like Google or Facebook."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                auth_provider_type_registry, AuthProviderSerializer
            ),
            400: get_error_schema(["ERROR_REQUEST_BODY_VALIDATION"]),
        },
    )
    @transaction.atomic
    @validate_body_custom_fields(
        auth_provider_type_registry,
        base_serializer_class=CreateAuthProviderSerializer,
    )
    @map_exceptions(
        {
            CannotCreateAuthProvider: ERROR_AUTH_PROVIDER_CANNOT_BE_CREATED,
        }
    )
    def post(self, request: Request, data: Dict[str, Any]) -> Response:
        """Create a new authentication provider."""

        check_sso_feature_is_active_or_raise()

        provider_type = data.pop("type")
        auth_provider_type = auth_provider_type_registry.get(provider_type)

        with auth_provider_type.map_api_exceptions():
            provider = AuthProviderHandler.create_auth_provider(
                request.user, auth_provider_type, **data
            )

        return Response(
            auth_provider_type.get_serializer(provider, AuthProviderSerializer).data
        )

    @extend_schema(
        tags=["Auth"],
        request=None,
        operation_id="list_auth_providers",
        description=("List all the available authentication providers."),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                auth_provider_type_registry, AuthProviderSerializer, many=True
            )
        },
    )
    @transaction.atomic
    def get(self, request: Request) -> Response:
        """List all authentication providers."""

        check_sso_feature_is_active_or_raise()

        auth_providers = []
        for auth_provider_type in auth_provider_type_registry.get_all():
            auth_providers.append(auth_provider_type.export_serialized())

        return Response({"auth_provider_types": auth_providers})


class AdminAuthProviderView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="auth_provider_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The authentication provider id to update.",
            ),
        ],
        tags=["Auth"],
        operation_id="update_auth_provider",
        description=(
            "Updates a new authentication provider. This can be used to enable "
            "authentication with a third party service like Google or Facebook."
        ),
        request=None,
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                auth_provider_type_registry, AuthProviderSerializer
            ),
            400: get_error_schema(["ERROR_REQUEST_BODY_VALIDATION"]),
            404: get_error_schema(["ERROR_AUTH_PROVIDER_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            AuthProviderModelNotFound: ERROR_AUTH_PROVIDER_DOES_NOT_EXIST,
            CannotDisableLastAuthProvider: ERROR_CANNOT_DISABLE_ALL_AUTH_PROVIDERS,
        }
    )
    def patch(self, request, auth_provider_id: int):
        """Update a new authentication provider."""

        check_sso_feature_is_active_or_raise()

        handler = AuthProviderHandler
        provider = handler.get_auth_provider_by_id(auth_provider_id)

        provider_type = provider.get_type()

        data = validate_data_custom_fields(
            provider_type.type,
            auth_provider_type_registry,
            request.data,
            base_serializer_class=UpdateAuthProviderSerializer,
        )
        with provider_type.map_api_exceptions():
            provider = handler.update_auth_provider(request.user, provider, **data)

        return Response(
            provider_type.get_serializer(provider, AuthProviderSerializer).data
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="auth_provider_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The authentication provider id to fetch.",
            ),
        ],
        tags=["Auth"],
        operation_id="get_auth_provider",
        description=("Get an authentication provider."),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                auth_provider_type_registry, AuthProviderSerializer
            ),
            404: get_error_schema(["ERROR_AUTH_PROVIDER_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            AuthProviderModelNotFound: ERROR_AUTH_PROVIDER_DOES_NOT_EXIST,
        }
    )
    def get(self, request: Request, auth_provider_id: int) -> Response:
        """Get the requested authentication providers."""

        check_sso_feature_is_active_or_raise()

        provider = AuthProviderHandler.get_auth_provider_by_id(auth_provider_id)
        return Response(
            provider.get_type()
            .get_serializer(provider, base_class=AuthProviderSerializer)
            .data
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="auth_provider_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The authentication provider id to delete.",
            ),
        ],
        tags=["Auth"],
        operation_id="delete_auth_provider",
        description=("Delete an authentication provider."),
        responses={
            204: None,
            404: get_error_schema(["ERROR_AUTH_PROVIDER_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            AuthProviderModelNotFound: ERROR_AUTH_PROVIDER_DOES_NOT_EXIST,
            CannotDeleteAuthProvider: ERROR_AUTH_PROVIDER_CANNOT_BE_DELETED,
            CannotDisableLastAuthProvider: ERROR_CANNOT_DISABLE_ALL_AUTH_PROVIDERS,
        }
    )
    def delete(self, request: Request, auth_provider_id: int) -> Response:
        """Delete the requested authentication provider."""

        check_sso_feature_is_active_or_raise()

        provider = AuthProviderHandler.get_auth_provider_by_id(auth_provider_id)
        AuthProviderHandler.delete_auth_provider(request.user, provider)

        return Response(status=204)


class AdminNextAuthProviderIdView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        exclude=True,
        tags=["Auth"],
        request=None,
        operation_id="get_next_auth_provider_id",
        description=("Returns the guessed next provider's id."),
        responses={200: NextAuthProviderIdSerializer},
    )
    @transaction.atomic
    def get(self, request: Request) -> Response:
        """Returns the guessed next provider's id."""

        check_sso_feature_is_active_or_raise()

        return Response({"next_provider_id": AuthProviderModel.get_next_provider_id()})

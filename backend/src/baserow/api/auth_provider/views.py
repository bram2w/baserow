from typing import Any, Dict
from urllib.request import Request

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.core.registries import auth_provider_type_registry


class AuthProvidersLoginOptionsView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Auth"],
        operation_id="list_auth_providers_login_options",
        description=(
            "Lists the available login options for the configured "
            "authentication providers."
        ),
        responses={
            200: Dict[str, Any],
        },
    )
    def get(self, request: Request) -> Response:
        """
        Lists the available login options for the configured authentication
        providers.
        """

        return Response(auth_provider_type_registry.get_all_available_login_options())

from typing import Dict

from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.applications.errors import ERROR_APPLICATION_DOES_NOT_EXIST
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from baserow.contrib.builder.api.theme.serializers import (
    CombinedThemeConfigBlocksRequestSerializer,
    CombinedThemeConfigBlocksSerializer,
    serialize_builder_theme,
)
from baserow.contrib.builder.handler import BuilderHandler
from baserow.contrib.builder.theme.service import ThemeService
from baserow.core.exceptions import ApplicationDoesNotExist


class ThemeView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="builder_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description=(
                    "Updates the theme for the application builder related to the "
                    "provided value."
                ),
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder theme"],
        operation_id="update_builder_theme",
        description="Updates the theme properties for the provided id.",
        request=CombinedThemeConfigBlocksSerializer,
        responses={
            200: CombinedThemeConfigBlocksSerializer,
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
        }
    )
    @validate_body(
        CombinedThemeConfigBlocksRequestSerializer, return_validated=True, partial=True
    )
    def patch(self, request, data: Dict, builder_id: int):
        builder = BuilderHandler().get_builder(builder_id)

        builder = ThemeService().update_theme(
            request.user,
            builder,
            **data,
        )

        return Response(serialize_builder_theme(builder))

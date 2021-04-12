from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes

from baserow.api.decorators import validate_body, map_exceptions
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.core.exceptions import UserNotInGroup
from baserow.core.handler import CoreHandler
from baserow.contrib.database.api.errors import ERROR_DATABASE_DOES_NOT_BELONG_TO_GROUP
from baserow.contrib.database.api.tables.errors import (
    ERROR_TABLE_DOES_NOT_BELONG_TO_GROUP,
)
from baserow.contrib.database.exceptions import DatabaseDoesNotBelongToGroup
from baserow.contrib.database.table.exceptions import TableDoesNotBelongToGroup
from baserow.contrib.database.tokens.exceptions import TokenDoesNotExist
from baserow.contrib.database.tokens.models import Token
from baserow.contrib.database.tokens.handler import TokenHandler

from .serializers import TokenSerializer, TokenCreateSerializer, TokenUpdateSerializer
from .errors import ERROR_TOKEN_DOES_NOT_EXIST


class TokensView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Database tokens"],
        operation_id="list_database_tokens",
        description=(
            "Lists all the API tokens that belong to the authorized user. An API token "
            "can be used to create, read, update and delete rows in the tables of the "
            "token's group. It only works on the tables if the token has the correct "
            "permissions. The **Database table rows** endpoints can be used for these "
            "operations."
        ),
        responses={
            200: TokenSerializer(many=True),
        },
    )
    def get(self, request):
        """Lists all the tokens of a user."""

        tokens = Token.objects.filter(user=request.user).prefetch_related(
            "tokenpermission_set"
        )
        serializer = TokenSerializer(tokens, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Database tokens"],
        operation_id="create_database_token",
        description=(
            "Creates a new API token for a given group and for the authorized user."
        ),
        request=TokenCreateSerializer,
        responses={
            200: TokenSerializer,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_REQUEST_BODY_VALIDATION"]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions({UserNotInGroup: ERROR_USER_NOT_IN_GROUP})
    @validate_body(TokenCreateSerializer)
    def post(self, request, data):
        """Creates a new token for the authorized user."""

        data["group"] = CoreHandler().get_group(data.pop("group"))
        token = TokenHandler().create_token(request.user, **data)
        serializer = TokenSerializer(token)
        return Response(serializer.data)


class TokenView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the token related to the provided value.",
            )
        ],
        tags=["Database tokens"],
        operation_id="get_database_token",
        description=(
            "Returns the requested token if it is owned by the authorized user and"
            "if the user has access to the related group."
        ),
        responses={
            200: TokenSerializer,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_TOKEN_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            TokenDoesNotExist: ERROR_TOKEN_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request, token_id):
        """Responds with a serialized token instance."""

        token = TokenHandler().get_token(request.user, token_id)
        serializer = TokenSerializer(token)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the token related to the provided value.",
            )
        ],
        tags=["Database tokens"],
        operation_id="update_database_token",
        description=(
            "Updates the existing token if it is owned by the authorized user and if"
            "the user has access to the related group."
        ),
        request=TokenUpdateSerializer,
        responses={
            200: TokenSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_DATABASE_DOES_NOT_BELONG_TO_GROUP",
                    "ERROR_TABLE_DOES_NOT_BELONG_TO_GROUP",
                ]
            ),
            404: get_error_schema(["ERROR_TOKEN_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            TokenDoesNotExist: ERROR_TOKEN_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            DatabaseDoesNotBelongToGroup: ERROR_DATABASE_DOES_NOT_BELONG_TO_GROUP,
            TableDoesNotBelongToGroup: ERROR_TABLE_DOES_NOT_BELONG_TO_GROUP,
        }
    )
    @validate_body(TokenUpdateSerializer)
    def patch(self, request, data, token_id):
        """Updates the values of a token."""

        token = TokenHandler().get_token(
            request.user, token_id, base_queryset=Token.objects.select_for_update()
        )
        permissions = data.pop("permissions", None)
        rotate_key = data.pop("rotate_key", False)

        if len(data) > 0:
            token = TokenHandler().update_token(request.user, token, **data)

        if permissions:
            TokenHandler().update_token_permissions(request.user, token, **permissions)

        if rotate_key:
            token = TokenHandler().rotate_token_key(request.user, token)

        serializer = TokenSerializer(token)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Deletes the token related to the provided value.",
            )
        ],
        tags=["Database tokens"],
        operation_id="delete_database_token",
        description=(
            "Deletes the existing token if it is owned by the authorized user and if"
            "the user has access to the related group."
        ),
        responses={
            204: None,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_TOKEN_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            TokenDoesNotExist: ERROR_TOKEN_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def delete(self, request, token_id):
        """Deletes an existing token."""

        token = TokenHandler().get_token(request.user, token_id)
        TokenHandler().delete_token(request.user, token)
        return Response(status=204)

from django.db import transaction
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from requests import RequestException
from advocate import UnacceptableAddressException

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.contrib.database.api.tables.errors import ERROR_TABLE_DOES_NOT_EXIST
from baserow.contrib.database.api.webhooks.errors import (
    ERROR_TABLE_WEBHOOK_DOES_NOT_EXIST,
    ERROR_TABLE_WEBHOOK_MAX_LIMIT_EXCEEDED,
)
from baserow.contrib.database.webhooks.exceptions import (
    TableWebhookDoesNotExist,
    TableWebhookMaxAllowedCountExceeded,
)
from baserow.contrib.database.webhooks.handler import WebhookHandler
from baserow.contrib.database.webhooks.models import TableWebhook
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.table.handler import TableHandler
from baserow.core.exceptions import UserNotInGroup
from .serializers import (
    TableWebhookCreateRequestSerializer,
    TableWebhookSerializer,
    TableWebhookUpdateRequestSerializer,
    TableWebhookTestCallRequestSerializer,
    TableWebhookTestCallResponseSerializer,
)


class TableWebhooksView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only webhooks of the table related to this value.",
            ),
        ],
        tags=["Database table webhooks"],
        operation_id="list_database_table_webhooks",
        description=(
            "Lists all webhooks of the table related to the provided `table_id` if the "
            "user has access to the related database group."
        ),
        responses={
            200: TableWebhookSerializer(many=True),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
        }
    )
    def get(self, request, table_id):
        """Lists all the webhooks of a given table."""

        table = TableHandler().get_table(table_id)
        webhook_handler = WebhookHandler()
        webhooks = webhook_handler.get_all_table_webhooks(
            table=table, user=request.user
        )
        return Response(TableWebhookSerializer(webhooks, many=True).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description=(
                    "Creates a webhook for the table related to the provided value."
                ),
            ),
        ],
        tags=["Database table webhooks"],
        operation_id="create_database_table_webhook",
        description=(
            "Creates a new webhook for the table related to the provided `table_id` "
            "parameter if the authorized user has access to the related database "
            "group."
        ),
        request=TableWebhookCreateRequestSerializer(),
        responses={
            200: TableWebhookSerializer(),
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_TABLE_WEBHOOK_MAX_LIMIT_EXCEEDED"]
            ),
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            TableWebhookMaxAllowedCountExceeded: ERROR_TABLE_WEBHOOK_MAX_LIMIT_EXCEEDED,
        }
    )
    @validate_body(TableWebhookCreateRequestSerializer)
    def post(self, request, data, table_id):
        """Creates a new webhook for a given table."""

        table = TableHandler().get_table(table_id)
        webhook_handler = WebhookHandler()
        webhook = webhook_handler.create_table_webhook(
            user=request.user, table=table, **data
        )
        return Response(TableWebhookSerializer(webhook).data)


class TableWebhookView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="webhook_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the webhook related to the provided value.",
            ),
        ],
        tags=["Database table webhooks"],
        operation_id="get_database_table_webhook",
        description=(
            "Returns the existing webhook if the authorized user has access to the "
            "related database group."
        ),
        responses={
            200: TableWebhookSerializer(),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_TABLE_WEBHOOK_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            TableWebhookDoesNotExist: ERROR_TABLE_WEBHOOK_DOES_NOT_EXIST,
        }
    )
    def get(self, request, webhook_id):
        webhook = WebhookHandler().get_table_webhook(request.user, webhook_id)
        return Response(TableWebhookSerializer(webhook).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="webhook_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the webhook related to the provided value.",
            ),
        ],
        tags=["Database table webhooks"],
        operation_id="update_database_table_webhook",
        description=(
            "Updates the existing view if the authorized user has access to the "
            "related database group."
        ),
        request=TableWebhookUpdateRequestSerializer(),
        responses={
            200: TableWebhookSerializer(),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_TABLE_WEBHOOK_DOES_NOT_EXIST"]),
        },
    )
    @validate_body(TableWebhookUpdateRequestSerializer)
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            TableWebhookDoesNotExist: ERROR_TABLE_WEBHOOK_DOES_NOT_EXIST,
        }
    )
    @transaction.atomic
    def patch(self, request, data, webhook_id):
        handler = WebhookHandler()
        webhook = handler.get_table_webhook(
            request.user,
            webhook_id,
            base_queryset=TableWebhook.objects.select_for_update(),
        )
        webhook = handler.update_table_webhook(
            user=request.user, webhook=webhook, **data
        )
        return Response(TableWebhookSerializer(webhook).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="webhook_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Deletes the webhook related to the provided value.",
            ),
        ],
        tags=["Database table webhooks"],
        operation_id="delete_database_table_webhook",
        description=(
            "Deletes the existing webhook if the authorized user has access to the "
            "related database's group."
        ),
        request=TableWebhookCreateRequestSerializer(),
        responses={
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_TABLE_WEBHOOK_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            TableWebhookDoesNotExist: ERROR_TABLE_WEBHOOK_DOES_NOT_EXIST,
        }
    )
    @transaction.atomic
    def delete(self, request, webhook_id):
        handler = WebhookHandler()
        webhook = handler.get_table_webhook(
            request.user,
            webhook_id,
            base_queryset=TableWebhook.objects.select_for_update(),
        )
        handler.delete_table_webhook(webhook=webhook, user=request.user)
        return Response(status=204)


class TableWebhookTestCallView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the table that must be tested.",
            ),
        ],
        tags=["Database table webhooks"],
        operation_id="test_call_database_table_webhook",
        description=(
            "This endpoint triggers a test call based on the provided data if the "
            "user has access to the group related to the table. The test call will be "
            "made immediately and a copy of the request, response and status will be "
            "included in the response."
        ),
        request=TableWebhookTestCallRequestSerializer,
        responses={
            200: TableWebhookTestCallResponseSerializer(),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
        }
    )
    @validate_body(TableWebhookTestCallRequestSerializer)
    def post(self, request, data, table_id):
        table = TableHandler().get_table(table_id)

        try:
            response = WebhookHandler().trigger_test_call(request.user, table, **data)
            data = {"response": response, "request": response.request}
        except RequestException as exception:
            data = {"request": exception.request}
        except UnacceptableAddressException:
            data = {}

        return Response(TableWebhookTestCallResponseSerializer(data).data)

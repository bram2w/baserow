from django.conf import settings
from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from baserow.api.decorators import validate_body
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.api.notifications.errors import ERROR_NOTIFICATION_DOES_NOT_EXIST
from baserow.api.schemas import get_error_schema
from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.api.utils import map_exceptions
from baserow.core.exceptions import UserNotInWorkspace, WorkspaceDoesNotExist
from baserow.core.notifications.exceptions import NotificationDoesNotExist
from baserow.core.notifications.service import NotificationService

from .serializers import NotificationRecipientSerializer, NotificationUpdateSerializer


class NotificationsView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The workspace id that the notifications belong to.",
            ),
            OpenApiParameter(
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines how many notifications should be returned.",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description=(
                    "Defines the offset of the notifications that should be returned."
                ),
            ),
        ],
        tags=["Notifications"],
        operation_id="list_workspace_notifications",
        description=(
            "Lists the notifications for the given workspace and the current user. "
            "The response is paginated and the limit and offset parameters can be "
            "controlled using the query parameters."
        ),
        responses={
            200: get_example_pagination_serializer_class(
                NotificationRecipientSerializer
            ),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
        }
    )
    def get(self, request: Request, workspace_id: int) -> Response:
        """
        Lists the notifications for the given workspace for the current user.
        The response is paginated and the limit and offset can be controlled
        using the query parameters.
        """

        paginator = LimitOffsetPagination()
        paginator.max_limit = settings.ROW_PAGE_SIZE_LIMIT
        paginator.default_limit = settings.ROW_PAGE_SIZE_LIMIT

        notifications = NotificationService.list_notifications(
            request.user, workspace_id
        )

        page = paginator.paginate_queryset(notifications, request, self)
        return paginator.get_paginated_response(
            NotificationRecipientSerializer(page, many=True).data
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The workspace the notifications are in.",
            ),
        ],
        tags=["Notifications"],
        operation_id="clear_workspace_notifications",
        description=("Clear all the notifications for the given workspace and user."),
        responses={
            204: None,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
        }
    )
    def delete(self, request: Request, workspace_id: int) -> Response:
        """
        Delete all the notifications for the given workspace and user.
        """

        NotificationService.clear_all_notifications(request.user, workspace_id)
        return Response(status=HTTP_204_NO_CONTENT)


class NotificationView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The workspace the notification is in.",
            ),
            OpenApiParameter(
                name="notification_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The notification id to update.",
            ),
        ],
        tags=["Notifications"],
        operation_id="mark_notification_as_read",
        description=("Marks a notification as read."),
        responses={
            200: NotificationRecipientSerializer,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(
                ["ERROR_GROUP_DOES_NOT_EXIST", "NOTIFICATION_DOES_NOT_EXIST"]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            NotificationDoesNotExist: ERROR_NOTIFICATION_DOES_NOT_EXIST,
        }
    )
    @validate_body(NotificationUpdateSerializer)
    def patch(
        self, request: Request, data, workspace_id: int, notification_id: int
    ) -> Response:
        """
        Updates the notification with the given id.
        """

        notification_recipient = NotificationService.mark_notification_as_read(
            request.user, workspace_id, notification_id, data["read"]
        )

        return Response(NotificationRecipientSerializer(notification_recipient).data)


class NotificationMarkAllAsReadView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The workspace the notifications are in.",
            ),
        ],
        tags=["Notifications"],
        operation_id="mark_all_workspace_notifications_as_read",
        description=(
            "Mark as read all the notifications for the given workspace and user."
        ),
        responses={
            204: None,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
        }
    )
    def post(self, request: Request, workspace_id: int) -> Response:
        """
        Marks all notifications as read for the given workspace and user.
        """

        NotificationService.mark_all_notifications_as_read(request.user, workspace_id)
        return Response(status=HTTP_204_NO_CONTENT)

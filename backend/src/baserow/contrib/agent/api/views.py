from uuid import UUID

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.applications.errors import ERROR_APPLICATION_DOES_NOT_EXIST
from baserow.api.applications.serializers import (
    PolymorphicApplicationResponseSerializer,
)
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.contrib.agent.actions import (
    CreateAgentConversationActionType,
    CreateAgentMessageActionType,
    UpdateAgentConfigurationActionType,
)
from baserow.contrib.agent.exceptions import (
    AgentConversationDoesNotExist,
    AgentMessageConflict,
    AgentNotReady,
)
from baserow.contrib.agent.models import AgentApplication
from baserow.contrib.agent.service import AgentService
from baserow.contrib.agent.signals import agent_loaded
from baserow.core.exceptions import ApplicationDoesNotExist, UserNotInWorkspace
from baserow.core.service import CoreService

from .errors import (
    ERROR_AGENT_CONVERSATION_DOES_NOT_EXIST,
    ERROR_AGENT_MESSAGE_CONFLICT,
    ERROR_AGENT_NOT_READY,
)
from .serializers import (
    AgentConfigurationSerializer,
    AgentConfigurationUpdateSerializer,
    AgentConversationCreateSerializer,
    AgentConversationPagination,
    AgentConversationSerializer,
    AgentMessageCreatedSerializer,
    AgentMessageCreateSerializer,
    AgentMessagePagination,
    AgentMessageSerializer,
)

AGENT_ID_PATH_PARAMETER = OpenApiParameter(
    name="agent_id",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="The id of the agent.",
)
AGENT_EXCEPTIONS = {
    ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
    AgentConversationDoesNotExist: ERROR_AGENT_CONVERSATION_DOES_NOT_EXIST,
    AgentNotReady: ERROR_AGENT_NOT_READY,
    AgentMessageConflict: ERROR_AGENT_MESSAGE_CONFLICT,
}
READ_ERRORS = {
    401: get_error_schema(["ERROR_PERMISSION_DENIED"]),
    404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
}
CONVERSATION_READ_ERRORS = {
    **READ_ERRORS,
    404: get_error_schema(
        ["ERROR_APPLICATION_DOES_NOT_EXIST", "ERROR_AGENT_CONVERSATION_DOES_NOT_EXIST"]
    ),
}
CONVERSATION_WRITE_ERRORS = {
    **CONVERSATION_READ_ERRORS,
    400: get_error_schema(["ERROR_REQUEST_BODY_VALIDATION", "ERROR_AGENT_NOT_READY"]),
    409: get_error_schema(["ERROR_AGENT_MESSAGE_CONFLICT"]),
}


class AgentApplicationView(APIView):
    def _get_agent_and_record_visit(
        self, request: Request, agent_id: int
    ) -> AgentApplication:
        agent = CoreService().get_application(
            request.user, agent_id, base_queryset=AgentApplication.objects
        )
        agent_loaded.send(sender=self, agent_id=agent.id, user=request.user)
        return agent

    @extend_schema(
        parameters=[AGENT_ID_PATH_PARAMETER],
        tags=["Agent applications"],
        operation_id="get_agent_application",
        description=(
            "Returns the agent, including its readiness, and records that the user "
            "opened it."
        ),
        responses={
            200: PolymorphicApplicationResponseSerializer,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            **READ_ERRORS,
        },
    )
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request: Request, agent_id: int) -> Response:
        """Responds with the agent if the user can read it."""

        agent = self._get_agent_and_record_visit(request, agent_id)
        return Response(
            PolymorphicApplicationResponseSerializer(
                agent, context={"request": request}
            ).data
        )

    @extend_schema(
        parameters=[AGENT_ID_PATH_PARAMETER],
        tags=["Agent applications"],
        operation_id="load_agent_application",
        description="Records that the user opened the agent.",
        request=None,
        responses={
            204: None,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            **READ_ERRORS,
        },
    )
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def post(self, request: Request, agent_id: int) -> Response:
        """Record the visit without serializing an already-loaded application."""

        self._get_agent_and_record_visit(request, agent_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgentConfigurationView(APIView):
    @extend_schema(
        parameters=[AGENT_ID_PATH_PARAMETER],
        tags=["Agent applications"],
        operation_id="get_agent_configuration",
        description=(
            "Returns the instructions, provider and model of the agent, with its "
            "readiness and the fields that are missing or no longer available."
        ),
        responses={200: AgentConfigurationSerializer, **READ_ERRORS},
    )
    @map_exceptions(AGENT_EXCEPTIONS)
    def get(self, request: Request, agent_id: int) -> Response:
        """Responds with the configuration if the user can read it."""

        configuration = AgentService().get_configuration(request.user, agent_id)
        return Response(AgentConfigurationSerializer(configuration).data)

    @extend_schema(
        parameters=[AGENT_ID_PATH_PARAMETER],
        tags=["Agent applications"],
        operation_id="update_agent_configuration",
        description=(
            "Updates the provided fields of the agent configuration and returns the "
            "result. An incomplete configuration can be saved and finished later."
        ),
        request=AgentConfigurationUpdateSerializer,
        responses={
            200: AgentConfigurationSerializer,
            **READ_ERRORS,
            400: get_error_schema(["ERROR_REQUEST_BODY_VALIDATION"]),
        },
    )
    @map_exceptions(AGENT_EXCEPTIONS)
    @validate_body(
        AgentConfigurationUpdateSerializer, partial=True, return_validated=True
    )
    def patch(self, request: Request, agent_id: int, data: dict) -> Response:
        """Updates the configuration if the user can both update and read it."""

        configuration = UpdateAgentConfigurationActionType.do(
            request.user, agent_id, **data
        )
        return Response(AgentConfigurationSerializer(configuration).data)


class AgentConversationsView(APIView):
    @extend_schema(
        tags=["Agent applications"],
        operation_id="list_agent_conversations",
        parameters=[
            AGENT_ID_PATH_PARAMETER,
            OpenApiParameter("page", OpenApiTypes.INT, default=1),
            OpenApiParameter(
                "size",
                OpenApiTypes.INT,
                default=20,
                description="Number of conversations per page, up to 100.",
            ),
        ],
        responses={
            200: get_example_pagination_serializer_class(AgentConversationSerializer),
            **READ_ERRORS,
        },
    )
    @map_exceptions(AGENT_EXCEPTIONS)
    def get(self, request: Request, agent_id: int) -> Response:
        """Paginate only the authenticated owner's conversations."""

        conversations = AgentService().list_conversations(request.user, agent_id)
        paginator = AgentConversationPagination(limit_page_size=100)
        page = paginator.paginate_queryset(conversations, request, self)
        return paginator.get_paginated_response(
            AgentConversationSerializer(page, many=True).data
        )

    @extend_schema(
        tags=["Agent applications"],
        operation_id="create_agent_conversation",
        request=AgentConversationCreateSerializer,
        responses={200: AgentMessageCreatedSerializer, **CONVERSATION_WRITE_ERRORS},
    )
    @map_exceptions(AGENT_EXCEPTIONS)
    @validate_body(AgentConversationCreateSerializer, return_validated=True)
    def post(self, request: Request, agent_id: int, data: dict) -> Response:
        """Starts a private conversation with its first message."""

        result = CreateAgentConversationActionType.do(request.user, agent_id, **data)
        return Response(AgentMessageCreatedSerializer(result).data)


class AgentMessagesView(APIView):
    @extend_schema(
        tags=["Agent applications"],
        operation_id="list_agent_messages",
        parameters=[
            AGENT_ID_PATH_PARAMETER,
            OpenApiParameter("page", OpenApiTypes.INT, default=1),
            OpenApiParameter(
                "size",
                OpenApiTypes.INT,
                default=50,
                description="Number of messages per page, up to 100.",
            ),
        ],
        responses={
            200: get_example_pagination_serializer_class(AgentMessageSerializer),
            **CONVERSATION_READ_ERRORS,
        },
    )
    @map_exceptions(AGENT_EXCEPTIONS)
    def get(self, request: Request, agent_id: int, conversation_uuid: UUID) -> Response:
        """Lists messages in pages from the newest, each in chronological order."""

        messages = AgentService().list_messages(
            request.user, agent_id, conversation_uuid
        )
        paginator = AgentMessagePagination(limit_page_size=100)
        page = paginator.paginate_queryset(messages, request, self)
        return paginator.get_paginated_response(
            AgentMessageSerializer(list(reversed(page)), many=True).data
        )

    @extend_schema(
        tags=["Agent applications"],
        operation_id="create_agent_message",
        request=AgentMessageCreateSerializer,
        responses={200: AgentMessageCreatedSerializer, **CONVERSATION_WRITE_ERRORS},
    )
    @map_exceptions(AGENT_EXCEPTIONS)
    @validate_body(AgentMessageCreateSerializer, return_validated=True)
    def post(
        self, request: Request, agent_id: int, conversation_uuid: UUID, data: dict
    ) -> Response:
        """Accept an authorized owner's message or recover its identical retry."""

        result = CreateAgentMessageActionType.do(
            request.user, agent_id, conversation_uuid, **data
        )
        return Response(AgentMessageCreatedSerializer(result).data)

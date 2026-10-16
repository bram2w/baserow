from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
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
from baserow.contrib.agent.models import AgentApplication
from baserow.contrib.agent.signals import agent_loaded
from baserow.core.exceptions import ApplicationDoesNotExist, UserNotInWorkspace
from baserow.core.service import CoreService

from ..actions import UpdateAgentConfigurationActionType
from ..handler import AgentHandler
from ..service import AgentService
from .serializers import (
    AgentConfigurationSerializer,
    AgentConfigurationUpdateSerializer,
    AgentReadinessSerializer,
)

AGENT_EXCEPTIONS = {ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST}
READ_ERRORS = {
    401: get_error_schema(["ERROR_PERMISSION_DENIED"]),
    404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
}


class AgentApplicationView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="agent_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the agent to open.",
            )
        ],
        tags=["Agent applications"],
        operation_id="get_agent_application",
        description="Returns the agent and records that the user opened it.",
        responses={
            200: PolymorphicApplicationResponseSerializer,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            401: get_error_schema(["ERROR_PERMISSION_DENIED"]),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
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

        agent = CoreService().get_application(
            request.user, agent_id, base_queryset=AgentApplication.objects
        )
        # The frontend requests the agent exactly once per agent visit.
        agent_loaded.send(sender=self, agent_id=agent.id, user=request.user)

        return Response(
            PolymorphicApplicationResponseSerializer(
                agent, context={"request": request}
            ).data
        )


class AgentReadinessView(APIView):
    @extend_schema(
        tags=["Agent applications"],
        operation_id="get_agent_readiness",
        responses={200: AgentReadinessSerializer, **READ_ERRORS},
    )
    @map_exceptions(AGENT_EXCEPTIONS)
    def get(self, request: Request, agent_id: int) -> Response:
        """Expose a coarse state without disclosing configuration values."""

        return Response(AgentService().get_readiness(request.user, agent_id))


class AgentConfigurationView(APIView):
    @extend_schema(
        tags=["Agent applications"],
        operation_id="get_agent_configuration",
        responses={200: AgentConfigurationSerializer, **READ_ERRORS},
    )
    @map_exceptions(AGENT_EXCEPTIONS)
    def get(self, request: Request, agent_id: int) -> Response:
        """Load settings only after the application-scoped Builder permission check."""

        return Response(AgentService().get_configuration(request.user, agent_id))

    @extend_schema(
        tags=["Agent applications"],
        operation_id="update_agent_configuration",
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
        """Save one partial draft and return the privileged validation envelope."""

        agent = UpdateAgentConfigurationActionType.do(request.user, agent_id, **data)
        return Response(AgentHandler().get_configuration(agent))

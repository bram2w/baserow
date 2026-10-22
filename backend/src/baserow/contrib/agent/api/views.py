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
from baserow.contrib.agent.actions import UpdateAgentConfigurationActionType
from baserow.contrib.agent.models import AgentApplication
from baserow.contrib.agent.service import AgentService
from baserow.contrib.agent.signals import agent_loaded
from baserow.core.exceptions import ApplicationDoesNotExist, UserNotInWorkspace
from baserow.core.service import CoreService

from .serializers import (
    AgentConfigurationSerializer,
    AgentConfigurationUpdateSerializer,
)

AGENT_ID_PATH_PARAMETER = OpenApiParameter(
    name="agent_id",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="The id of the agent.",
)
AGENT_EXCEPTIONS = {ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST}
READ_ERRORS = {
    401: get_error_schema(["ERROR_PERMISSION_DENIED"]),
    404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
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

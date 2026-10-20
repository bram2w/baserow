from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.applications.errors import ERROR_APPLICATION_DOES_NOT_EXIST
from baserow.api.applications.serializers import (
    PolymorphicApplicationResponseSerializer,
)
from baserow.api.decorators import map_exceptions
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.contrib.agent.models import AgentApplication
from baserow.contrib.agent.signals import agent_loaded
from baserow.core.exceptions import ApplicationDoesNotExist, UserNotInWorkspace
from baserow.core.service import CoreService


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

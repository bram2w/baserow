from urllib.request import Request

from baserow_enterprise.role.actions import AssignRoleActionType
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.core.action.registries import action_type_registry
from baserow.core.exceptions import UserNotInGroup
from baserow.core.handler import CoreHandler

from .serializers import CreateRoleAssignmentSerializer, RoleAssignmentSerializer


class RoleAssignmentsView(APIView):
    """ """

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description=".",
            ),
        ],
        tags=["Group role assignments"],
        operation_id="enterprise_group_assign_role",
        description="",
        request=CreateRoleAssignmentSerializer,
        responses={
            200: RoleAssignmentSerializer,
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    @validate_body(CreateRoleAssignmentSerializer, return_validated=True)
    def post(
        self,
        request: Request,
        group_id: int,
        data,
    ) -> Response:
        """ """

        group = CoreHandler().get_group(group_id)

        role = data.get("role", None)

        if role is not None:
            # We set the role
            role_assignment = action_type_registry.get_by_type(AssignRoleActionType).do(
                request.user,
                data["subject"],
                group,
                role,
                scope=data["scope"],
            )

            serializer = RoleAssignmentSerializer(role_assignment)

            return Response(serializer.data)
        else:
            # We remove the role
            action_type_registry.get_by_type(AssignRoleActionType).do(
                request.user,
                data["subject"],
                group,
                role=None,
                scope=data["scope"],
            )
            return Response(status=204)

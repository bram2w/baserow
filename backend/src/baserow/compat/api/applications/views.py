from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema

from baserow.api.applications.errors import ERROR_APPLICATION_NOT_IN_GROUP
from baserow.api.applications.serializers import (
    ApplicationCreateSerializer,
    ApplicationSerializer,
    OrderApplicationsSerializer,
)
from baserow.api.applications.views import ApplicationsView, OrderApplicationsView
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import (
    CLIENT_SESSION_ID_SCHEMA_PARAMETER,
    CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
    get_error_schema,
)
from baserow.api.utils import DiscriminatorMappingSerializer
from baserow.compat.api.conf import (
    APPLICATION_DEPRECATION_PREFIXES as DEPRECATION_PREFIXES,
)
from baserow.core.exceptions import (
    ApplicationNotInWorkspace,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
)
from baserow.core.registries import application_type_registry

application_type_serializers = {
    application_type.type: (
        application_type.instance_serializer_class or ApplicationSerializer
    )
    for application_type in application_type_registry.registry.values()
}


class ApplicationsCompatView(ApplicationsView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only applications that are in the group related "
                "to the provided value.",
            )
        ],
        tags=["Applications"],
        operation_id="group_list_applications",
        deprecated=True,
        description=(
            f"{DEPRECATION_PREFIXES['group_list_applications']} Lists all the "
            "applications of the group related to the provided `group_id` parameter if "
            "the authorized user is in that group. If the group is related to a "
            "template, then this endpoint will be publicly accessible. The properties "
            "that belong to the application can differ per type. An application always "
            "belongs to a single group."
        ),
        responses={
            200: DiscriminatorMappingSerializer(
                "Applications", application_type_serializers, many=True
            ),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request, group_id):
        """
        Responds with a list of serialized applications that belong to the user. If a
        group id is provided only the applications of that group are going to be
        returned.
        """

        return super().get(request, group_id)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Creates an application for the group related to the "
                "provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Applications"],
        operation_id="group_create_application",
        deprecated=True,
        description=(
            f"{DEPRECATION_PREFIXES['group_create_application']} Creates a new "
            "application based on the provided type. The newly created application "
            "is going to be added to the group related to the provided `group_id` "
            "parameter. If the authorized user does not belong to the group an "
            "error will be returned."
        ),
        request=ApplicationCreateSerializer,
        responses={
            200: DiscriminatorMappingSerializer(
                "Applications", application_type_serializers
            ),
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_REQUEST_BODY_VALIDATION"]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(ApplicationCreateSerializer)
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def post(self, request, data, group_id):
        """Creates a new application for a user."""

        return super().post(request, workspace_id=group_id)


class OrderApplicationsCompatView(OrderApplicationsView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the order of the applications in the group "
                "related to the provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Applications"],
        operation_id="group_order_applications",
        deprecated=True,
        description=(
            f"{DEPRECATION_PREFIXES['group_order_applications']} Changes the order of "
            "the provided application ids to the matching position that the id has in "
            "the list. If the authorized user does not belong to the group it will be "
            "ignored. The order of the not provided tables will be set to `0`."
        ),
        request=OrderApplicationsSerializer,
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_APPLICATION_NOT_IN_GROUP"]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @validate_body(OrderApplicationsSerializer)
    @transaction.atomic
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ApplicationNotInWorkspace: ERROR_APPLICATION_NOT_IN_GROUP,
        }
    )
    def post(self, request, data, group_id):
        """Updates to order of the applications in a table."""

        return super().post(request, workspace_id=group_id)

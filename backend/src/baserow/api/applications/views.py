from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.applications.errors import (
    ERROR_APPLICATION_DOES_NOT_EXIST,
    ERROR_APPLICATION_NOT_IN_GROUP,
)
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.api.jobs.errors import ERROR_MAX_JOB_COUNT_EXCEEDED
from baserow.api.jobs.serializers import JobSerializer
from baserow.api.schemas import (
    CLIENT_SESSION_ID_SCHEMA_PARAMETER,
    CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
    get_error_schema,
)
from baserow.api.trash.errors import ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM
from baserow.api.utils import DiscriminatorMappingSerializer
from baserow.core.action.registries import action_type_registry
from baserow.core.actions import (
    CreateApplicationActionType,
    DeleteApplicationActionType,
    OrderApplicationsActionType,
    UpdateApplicationActionType,
)
from baserow.core.db import specific_iterator
from baserow.core.exceptions import (
    ApplicationDoesNotExist,
    ApplicationNotInGroup,
    GroupDoesNotExist,
    UserNotInGroup,
)
from baserow.core.handler import CoreHandler
from baserow.core.job_types import DuplicateApplicationJobType
from baserow.core.jobs.exceptions import MaxJobCountExceeded
from baserow.core.jobs.handler import JobHandler
from baserow.core.jobs.registries import job_type_registry
from baserow.core.models import Application, Group
from baserow.core.operations import (
    CreateApplicationsGroupOperationType,
    ListApplicationsGroupOperationType,
)
from baserow.core.registries import application_type_registry
from baserow.core.trash.exceptions import CannotDeleteAlreadyDeletedItem

from .serializers import (
    ApplicationCreateSerializer,
    ApplicationSerializer,
    ApplicationUpdateSerializer,
    OrderApplicationsSerializer,
    get_application_serializer,
)

application_type_serializers = {
    application_type.type: (
        application_type.instance_serializer_class or ApplicationSerializer
    )
    for application_type in application_type_registry.registry.values()
}

DuplicateApplicationJobTypeSerializer = job_type_registry.get(
    DuplicateApplicationJobType.type
).get_serializer_class(base_class=JobSerializer)


class AllApplicationsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Applications"],
        operation_id="list_all_applications",
        description=(
            "Lists all the applications that the authorized user has access to. The "
            "properties that belong to the application can differ per type. An "
            "application always belongs to a single group. All the applications of the "
            "groups that the user has access to are going to be listed here."
        ),
        responses={
            200: DiscriminatorMappingSerializer(
                "Applications", application_type_serializers, many=True
            ),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
        },
    )
    @map_exceptions({UserNotInGroup: ERROR_USER_NOT_IN_GROUP})
    def get(self, request):
        """
        Responds with a list of serialized applications that belong to the user. If a
        group id is provided only the applications of that group are going to be
        returned.
        """

        groups = Group.objects.filter(users=request.user)

        # Compute list of readable application ids
        applications_ids = []
        for group in groups:
            applications = Application.objects.filter(group=group, group__trashed=False)
            applications = CoreHandler().filter_queryset(
                request.user,
                ListApplicationsGroupOperationType.type,
                applications,
                group=group,
                context=group,
            )
            applications_ids += applications.values_list("id", flat=True)

        # Then filter with these ids
        applications = specific_iterator(
            Application.objects.select_related("content_type", "group")
            .filter(id__in=applications_ids)
            .order_by("group_id", "order")
        )

        data = [
            get_application_serializer(
                application, context={"request": request, "application": application}
            ).data
            for application in applications
        ]
        return Response(data)


class ApplicationsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        return super().get_permissions()

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
        operation_id="list_applications",
        description=(
            "Lists all the applications of the group related to the provided "
            "`group_id` parameter if the authorized user is in that group. If the"
            "group is related to a template, then this endpoint will be publicly "
            "accessible. The properties that belong to the application can differ per "
            "type. An application always belongs to a single group."
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
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request, group_id):
        """
        Responds with a list of serialized applications that belong to the user. If a
        group id is provided only the applications of that group are going to be
        returned.
        """

        group = CoreHandler().get_group(group_id)

        CoreHandler().check_permissions(
            request.user,
            ListApplicationsGroupOperationType.type,
            group=group,
            context=group,
            allow_if_template=True,
        )

        applications = Application.objects.select_related(
            "content_type", "group"
        ).filter(group=group)

        applications = CoreHandler().filter_queryset(
            request.user,
            ListApplicationsGroupOperationType.type,
            applications,
            group=group,
            context=group,
            allow_if_template=True,
        )

        data = [
            get_application_serializer(application, context={"request": request}).data
            for application in applications
        ]
        return Response(data)

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
        operation_id="create_application",
        description=(
            "Creates a new application based on the provided type. The newly created "
            "application is going to be added to the group related to the provided "
            "`group_id` parameter. If the authorized user does not belong to the group "
            "an error will be returned."
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
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def post(self, request, data, group_id):
        """Creates a new application for a user."""

        group = CoreHandler().get_group(group_id)

        CoreHandler().check_permissions(
            request.user,
            CreateApplicationsGroupOperationType.type,
            group=group,
            context=group,
        )

        application = action_type_registry.get_by_type(CreateApplicationActionType).do(
            request.user,
            group,
            data["type"],
            name=data["name"],
            init_with_data=data["init_with_data"],
        )

        return Response(
            get_application_serializer(application, context={"request": request}).data
        )


class ApplicationView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="application_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the application related to the provided value.",
            )
        ],
        tags=["Applications"],
        operation_id="get_application",
        description=(
            "Returns the requested application if the authorized user is in the "
            "application's group. The properties that belong to the application can "
            "differ per type."
        ),
        request=ApplicationCreateSerializer,
        responses={
            200: DiscriminatorMappingSerializer(
                "Applications", application_type_serializers
            ),
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_REQUEST_BODY_VALIDATION"]
            ),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request, application_id):
        """Selects a single application and responds with a serialized version."""

        application = CoreHandler().get_user_application(request.user, application_id)

        return Response(
            get_application_serializer(application, context={"request": request}).data
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="application_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the application related to the provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Applications"],
        operation_id="update_application",
        description=(
            "Updates the existing application related to the provided "
            "`application_id` param if the authorized user is in the application's "
            "group. It is not possible to change the type, but properties like the "
            "name can be changed."
        ),
        request=ApplicationUpdateSerializer,
        responses={
            200: DiscriminatorMappingSerializer(
                "Applications", application_type_serializers
            ),
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_REQUEST_BODY_VALIDATION"]
            ),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(ApplicationUpdateSerializer)
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def patch(self, request, data, application_id):
        """Updates the application if the user belongs to the group."""

        application = CoreHandler().get_application(
            application_id,
            base_queryset=Application.objects.select_for_update(of=("self",)),
        )

        application = action_type_registry.get_by_type(UpdateApplicationActionType).do(
            request.user, application, name=data["name"]
        )

        return Response(
            get_application_serializer(application, context={"request": request}).data
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="application_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Deletes the application related to the provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Applications"],
        operation_id="delete_application",
        description=(
            "Deletes an application if the authorized user is in the application's "
            "group. All the related children are also going to be deleted. For example "
            "in case of a database application all the underlying tables, fields, "
            "views and rows are going to be deleted."
        ),
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM"]
            ),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            CannotDeleteAlreadyDeletedItem: ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM,
        }
    )
    def delete(self, request, application_id):
        """Deletes an existing application if the user belongs to the group."""

        application = CoreHandler().get_application(
            application_id,
            base_queryset=Application.objects.select_for_update(of=("self",)),
        )

        action_type_registry.get_by_type(DeleteApplicationActionType).do(
            request.user, application
        )

        return Response(status=204)


class OrderApplicationsView(APIView):
    permission_classes = (IsAuthenticated,)

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
        operation_id="order_applications",
        description=(
            "Changes the order of the provided application ids to the matching "
            "position that the id has in the list. If the authorized user does not "
            "belong to the group it will be ignored. The order of the not provided "
            "tables will be set to `0`."
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
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            ApplicationNotInGroup: ERROR_APPLICATION_NOT_IN_GROUP,
        }
    )
    def post(self, request, data, group_id):
        """Updates to order of the applications in a table."""

        group = CoreHandler().get_group(group_id)
        action_type_registry.get_by_type(OrderApplicationsActionType).do(
            request.user, group, data["application_ids"]
        )
        return Response(status=204)


class AsyncDuplicateApplicationView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="application_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the application to duplicate.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Applications"],
        operation_id="duplicate_application_async",
        description=(
            "Duplicate an application if the authorized user is in the application's "
            "group. All the related children are also going to be duplicated. For example "
            "in case of a database application all the underlying tables, fields, "
            "views and rows are going to be duplicated."
        ),
        responses={
            202: DuplicateApplicationJobTypeSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_APPLICATION_NOT_IN_GROUP",
                    "ERROR_MAX_JOB_COUNT_EXCEEDED",
                ]
            ),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            MaxJobCountExceeded: ERROR_MAX_JOB_COUNT_EXCEEDED,
        }
    )
    def post(self, request: Request, application_id: int) -> Response:
        """
        Duplicates an existing application if the user belongs to the group.
        """

        job = JobHandler().create_and_start_job(
            request.user,
            DuplicateApplicationJobType.type,
            application_id=application_id,
        )

        serializer = job_type_registry.get_serializer(job, JobSerializer)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

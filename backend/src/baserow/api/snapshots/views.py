from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_202_ACCEPTED
from rest_framework.views import APIView

from baserow.api.applications.errors import (
    ERROR_APPLICATION_DOES_NOT_EXIST,
    ERROR_APPLICATION_OPERATION_NOT_SUPPORTED,
)
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.jobs.serializers import JobSerializer
from baserow.api.schemas import get_error_schema
from baserow.api.snapshots.errors import (
    ERROR_MAXIMUM_SNAPSHOTS_REACHED,
    ERROR_SNAPSHOT_DOES_NOT_EXIST,
    ERROR_SNAPSHOT_IS_BEING_CREATED,
    ERROR_SNAPSHOT_IS_BEING_DELETED,
    ERROR_SNAPSHOT_IS_BEING_RESTORED,
    ERROR_SNAPSHOT_NAME_NOT_UNIQUE,
    ERROR_SNAPSHOT_OPERATION_LIMIT_EXCEEDED,
)
from baserow.core.action.registries import action_type_registry
from baserow.core.exceptions import (
    ApplicationDoesNotExist,
    ApplicationOperationNotSupported,
    UserNotInWorkspace,
)
from baserow.core.jobs.exceptions import MaxJobCountExceeded
from baserow.core.snapshots.actions import DeleteSnapshotActionType
from baserow.core.snapshots.exceptions import (
    MaximumSnapshotsReached,
    SnapshotDoesNotExist,
    SnapshotIsBeingCreated,
    SnapshotIsBeingDeleted,
    SnapshotIsBeingRestored,
    SnapshotNameNotUnique,
)
from baserow.core.snapshots.handler import SnapshotHandler

from .serializers import SnapshotSerializer


class SnapshotsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="application_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Application ID for which to list snapshots.",
                required=True,
            )
        ],
        tags=["Snapshots"],
        operation_id="list_snapshots",
        description=("Lists snapshots that were created for a given application."),
        responses={
            200: SnapshotSerializer(many=True),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request, application_id):
        """
        Lists all snapshots created for a given application.
        """

        handler = SnapshotHandler()
        snapshots = handler.list(application_id, request.user)
        serializer = SnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="application_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Application ID for which to list snapshots.",
                required=True,
            )
        ],
        tags=["Snapshots"],
        operation_id="create_snapshot",
        description=(
            "Creates a new application snapshot. Snapshots represent a state of an "
            "application at a specific point in time and can be restored later, "
            "making it easy to create backups of entire applications."
        ),
        request=SnapshotSerializer,
        responses={
            202: JobSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_MAXIMUM_SNAPSHOTS_REACHED",
                    "ERROR_APPLICATION_OPERATION_NOT_SUPPORTED",
                    "ERROR_SNAPSHOT_IS_BEING_CREATED",
                    "ERROR_SNAPSHOT_NAME_NOT_UNIQUE",
                    "ERROR_SNAPSHOT_OPERATION_LIMIT_EXCEEDED",
                ]
            ),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            MaximumSnapshotsReached: ERROR_MAXIMUM_SNAPSHOTS_REACHED,
            ApplicationOperationNotSupported: ERROR_APPLICATION_OPERATION_NOT_SUPPORTED,
            SnapshotIsBeingCreated: ERROR_SNAPSHOT_IS_BEING_CREATED,
            SnapshotNameNotUnique: ERROR_SNAPSHOT_NAME_NOT_UNIQUE,
            MaxJobCountExceeded: ERROR_SNAPSHOT_OPERATION_LIMIT_EXCEEDED,
        }
    )
    @validate_body(SnapshotSerializer)
    @transaction.atomic
    def post(self, request, application_id, data):
        """
        Creates a new application snapshot.
        """

        handler = SnapshotHandler()
        snapshot_created = handler.start_create_job(
            application_id, request.user, data["name"]
        )
        serializer = JobSerializer(snapshot_created["job"])
        return Response(serializer.data, status=HTTP_202_ACCEPTED)


class RestoreSnapshotView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="snapshot_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Id of the snapshot to restore.",
            )
        ],
        tags=["Snapshots"],
        operation_id="restore_snapshot",
        description=(
            "Restores a snapshot. When an application snapshot is restored, "
            "a new application will be created in the same workspace that the original "
            "application was placed in with the name of the snapshot and data that were"
            " in the original application at the time the snapshot was taken. "
            "The original application that the snapshot was taken from is unaffected. "
            "Snapshots can be restored multiple times and a number suffix is added to "
            "the new application name in the case of a collision."
        ),
        request=None,
        responses={
            200: JobSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_APPLICATION_OPERATION_NOT_SUPPORTED",
                    "ERROR_SNAPSHOT_IS_BEING_RESTORED",
                    "ERROR_SNAPSHOT_IS_BEING_DELETED",
                    "ERROR_SNAPSHOT_OPERATION_LIMIT_EXCEEDED",
                ]
            ),
            404: get_error_schema(["ERROR_SNAPSHOT_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            SnapshotDoesNotExist: ERROR_SNAPSHOT_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ApplicationOperationNotSupported: ERROR_APPLICATION_OPERATION_NOT_SUPPORTED,
            SnapshotIsBeingRestored: ERROR_SNAPSHOT_IS_BEING_RESTORED,
            SnapshotIsBeingDeleted: ERROR_SNAPSHOT_IS_BEING_DELETED,
            MaxJobCountExceeded: ERROR_SNAPSHOT_OPERATION_LIMIT_EXCEEDED,
        }
    )
    @transaction.atomic
    def post(self, request, snapshot_id):
        """
        Restores a given application snapshot.
        """

        handler = SnapshotHandler()
        job = handler.start_restore_job(snapshot_id, request.user)
        serializer = JobSerializer(job)
        return Response(serializer.data)


class SnapshotView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="snapshot_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Id of the snapshot to delete.",
            )
        ],
        tags=["Snapshots"],
        operation_id="delete_snapshot",
        description=(
            "Deletes a snapshot. Deleting a snapshot doesn't affect the application "
            "that the snapshot is made from and doesn't affect any applications that "
            "were created by restoring it. Snapshot deletion is permanent and "
            "can't be undone."
        ),
        request=None,
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_APPLICATION_OPERATION_NOT_SUPPORTED",
                    "ERROR_SNAPSHOT_IS_BEING_RESTORED",
                    "ERROR_SNAPSHOT_IS_BEING_DELETED",
                    "ERROR_SNAPSHOT_OPERATION_LIMIT_EXCEEDED",
                ]
            ),
            404: get_error_schema(["ERROR_SNAPSHOT_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            SnapshotDoesNotExist: ERROR_SNAPSHOT_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ApplicationOperationNotSupported: ERROR_APPLICATION_OPERATION_NOT_SUPPORTED,
            SnapshotIsBeingRestored: ERROR_SNAPSHOT_IS_BEING_RESTORED,
            SnapshotIsBeingDeleted: ERROR_SNAPSHOT_IS_BEING_DELETED,
            MaxJobCountExceeded: ERROR_SNAPSHOT_OPERATION_LIMIT_EXCEEDED,
        }
    )
    @transaction.atomic
    def delete(self, request, snapshot_id):
        """
        Deletes a given application snapshot.
        """

        action_type_registry.get(DeleteSnapshotActionType.type).do(
            request.user, snapshot_id
        )
        return Response(status=204)

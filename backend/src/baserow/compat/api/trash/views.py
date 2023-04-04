from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from baserow.api.applications.errors import (
    ERROR_APPLICATION_DOES_NOT_EXIST,
    ERROR_APPLICATION_NOT_IN_GROUP,
)
from baserow.api.decorators import map_exceptions
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.api.trash.views import ExampleTrashContentsSerializer, TrashContentsView
from baserow.compat.api.conf import TRASH_DEPRECATION_PREFIXES as DEPRECATION_PREFIXES
from baserow.core.exceptions import (
    ApplicationDoesNotExist,
    ApplicationNotInWorkspace,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
)


class TrashContentsCompatView(TrashContentsView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the trash for the group with this id.",
            ),
            OpenApiParameter(
                name="application_id",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Optionally filters down the trash to only items for "
                "this application in the group.",
            ),
            OpenApiParameter(
                name="page",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Selects which page of trash contents should be returned.",
            ),
        ],
        tags=["Trash"],
        deprecated=True,
        operation_id="group_get_contents",
        description=(
            f"{DEPRECATION_PREFIXES['group_get_contents']} Responds with trash "
            "contents for a group optionally filtered to a specific application."
        ),
        responses={
            200: ExampleTrashContentsSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_APPLICATION_NOT_IN_GROUP",
                    "ERROR_GROUP_DOES_NOT_EXIST",
                    "ERROR_APPLICATION_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ApplicationNotInWorkspace: ERROR_APPLICATION_NOT_IN_GROUP,
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, group_id):
        """
        Responds with any trashed items in the group or application, including an
        entry for the group/app if they themselves are trashed.
        """

        return super().get(request, group_id)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The group whose trash contents to empty, including the "
                "group itself if it is also trashed.",
            ),
            OpenApiParameter(
                name="application_id",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Optionally filters down the trash to delete to only items "
                "for this application in the group.",
            ),
        ],
        tags=["Trash"],
        deprecated=True,
        operation_id="group_empty_contents",
        description=(
            f"{DEPRECATION_PREFIXES['group_empty_contents']} Empties the specified "
            "group and/or application of trash, including the group and application "
            "themselves if they are trashed also."
        ),
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_APPLICATION_NOT_IN_GROUP",
                    "ERROR_GROUP_DOES_NOT_EXIST",
                    "ERROR_APPLICATION_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ApplicationNotInWorkspace: ERROR_APPLICATION_NOT_IN_GROUP,
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
        }
    )
    def delete(self, request, group_id):
        """
        Empties the group and/or application of trash permanently deleting any
        trashed contents, including the group and application if they are also
        trashed.
        """

        return super().delete(request, group_id)

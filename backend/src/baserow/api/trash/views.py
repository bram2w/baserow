from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.applications.errors import (
    ERROR_APPLICATION_DOES_NOT_EXIST,
    ERROR_APPLICATION_NOT_IN_GROUP,
)
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import (
    ERROR_GROUP_DOES_NOT_EXIST,
    ERROR_USER_NOT_IN_GROUP,
)
from baserow.api.pagination import PageNumberPagination
from baserow.api.schemas import get_error_schema
from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.core.exceptions import (
    UserNotInGroup,
    ApplicationNotInGroup,
    GroupDoesNotExist,
    ApplicationDoesNotExist,
    TrashItemDoesNotExist,
)
from baserow.core.trash.handler import TrashHandler
from baserow.core.trash.exceptions import (
    CannotRestoreChildBeforeParent,
    ParentIdMustNotBeProvidedException,
    ParentIdMustBeProvidedException,
)

from .errors import (
    ERROR_CANNOT_RESTORE_PARENT_BEFORE_CHILD,
    ERROR_PARENT_ID_MUST_NOT_BE_PROVIDED,
    ERROR_PARENT_ID_MUST_BE_PROVIDED,
    ERROR_TRASH_ITEM_DOES_NOT_EXIST,
)
from .serializers import (
    TrashContentsSerializer,
    TrashStructureSerializer,
    TrashEntryRequestSerializer,
)


class TrashItemView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Trash"],
        operation_id="restore",
        description="Restores the specified trashed item back into baserow.",
        request=TrashEntryRequestSerializer,
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_TRASH_ITEM_DOES_NOT_EXIST",
                    "ERROR_CANNOT_RESTORE_PARENT_BEFORE_CHILD",
                    "ERROR_PARENT_ID_MUST_NOT_BE_PROVIDED",
                    "ERROR_PARENT_ID_MUST_BE_PROVIDED",
                ]
            ),
        },
    )
    @validate_body(TrashEntryRequestSerializer)
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            TrashItemDoesNotExist: ERROR_TRASH_ITEM_DOES_NOT_EXIST,
            CannotRestoreChildBeforeParent: ERROR_CANNOT_RESTORE_PARENT_BEFORE_CHILD,
            ParentIdMustNotBeProvidedException: ERROR_PARENT_ID_MUST_NOT_BE_PROVIDED,
            ParentIdMustBeProvidedException: ERROR_PARENT_ID_MUST_BE_PROVIDED,
        }
    )
    def patch(self, request, data):
        """
        Restores the specified trashable item if it is in the trash and the user is
        in the items group.
        """

        TrashHandler.restore_item(
            request.user,
            data["trash_item_type"],
            data["trash_item_id"],
            parent_trash_item_id=data.get("parent_trash_item_id", None),
        )
        return Response(status=204)


class TrashContentsView(APIView):
    permission_classes = (IsAuthenticated,)

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
        operation_id="get_contents",
        description="Responds with trash contents for a group optionally "
        "filtered to a specific application.",
        responses={
            200: get_example_pagination_serializer_class(TrashContentsSerializer),
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
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            ApplicationNotInGroup: ERROR_APPLICATION_NOT_IN_GROUP,
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, group_id):
        """
        Responds with any trashed items in the group or application, including an
        entry for the group/app if they themselves are trashed.
        """

        application_id = request.GET.get("application_id", None)
        trash_contents = TrashHandler.get_trash_contents(
            request.user, group_id, application_id
        )
        paginator = PageNumberPagination(limit_page_size=settings.TRASH_PAGE_SIZE_LIMIT)
        page = paginator.paginate_queryset(trash_contents, request, self)
        serializer = TrashContentsSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

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
        operation_id="empty_contents",
        description="Empties the specified group and/or application of trash, including"
        " the group and application themselves if they are trashed also.",
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
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            ApplicationNotInGroup: ERROR_APPLICATION_NOT_IN_GROUP,
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
        }
    )
    def delete(self, request, group_id):
        """
        Empties the group and/or application of trash permanently deleting any trashed
        contents, including the group and application if they are also trashed.
        """

        application_id = request.GET.get("application_id", None)
        TrashHandler.empty(request.user, group_id, application_id)
        return Response(status=204)


class TrashStructureView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Trash"],
        operation_id="get_trash_structure",
        description="Responds with the groups and applications available for the "
        "requesting user to inspect the trash contents of.",
        responses={
            200: TrashStructureSerializer,
        },
    )
    def get(self, request):
        """
        Responds with the structure of the trash for the user.
        """

        structure = TrashHandler.get_trash_structure(request.user)
        return Response(TrashStructureSerializer(structure).data)

from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import (
    map_exceptions,
    validate_body,
    validate_query_parameters,
)
from baserow.api.errors import (
    ERROR_GROUP_DOES_NOT_EXIST,
    ERROR_INVALID_SORT_ATTRIBUTE,
    ERROR_INVALID_SORT_DIRECTION,
    ERROR_USER_INVALID_GROUP_PERMISSIONS,
    ERROR_USER_NOT_IN_GROUP,
)
from baserow.api.exceptions import (
    InvalidSortAttributeException,
    InvalidSortDirectionException,
)
from baserow.api.groups.users.errors import (
    ERROR_CANNOT_DELETE_YOURSELF_FROM_GROUP,
    ERROR_GROUP_USER_DOES_NOT_EXIST,
)
from baserow.api.mixins import SearchableViewMixin, SortableViewMixin
from baserow.api.schemas import get_error_schema
from baserow.api.user.registries import member_data_registry
from baserow.core.exceptions import (
    CannotDeleteYourselfFromGroup,
    GroupDoesNotExist,
    GroupUserDoesNotExist,
    UserInvalidGroupPermissionsError,
    UserNotInGroup,
)
from baserow.core.handler import CoreHandler
from baserow.core.models import GroupUser
from baserow.core.operations import ListGroupUsersGroupOperationType

from .serializers import (
    GetGroupUsersViewParamsSerializer,
    GroupUserSerializer,
    UpdateGroupUserSerializer,
    get_list_group_user_serializer,
)

ListGroupUsersWithMemberDataSerializer = get_list_group_user_serializer()


class GroupUsersView(APIView, SearchableViewMixin, SortableViewMixin):
    search_fields = ["user__username", "user__email"]
    sort_field_mapping = {
        "name": "user__username",
        "email": "user__email",
        "role_uid": "permissions",
    }

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the group user related to the provided value.",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Search for group users by username, or email.",
            ),
            OpenApiParameter(
                name="sorts",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Sort group users by name, email or role.",
            ),
        ],
        tags=["Groups"],
        operation_id="list_group_users",
        description=(
            "Lists all the users that are in a group if the authorized user has admin "
            "permissions to the related group. To add a user to a group an invitation "
            "must be sent first."
        ),
        responses={
            200: ListGroupUsersWithMemberDataSerializer(many=True),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                    "ERROR_INVALID_SORT_DIRECTION",
                    "ERROR_INVALID_SORT_ATTRIBUTE",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
            InvalidSortDirectionException: ERROR_INVALID_SORT_DIRECTION,
            InvalidSortAttributeException: ERROR_INVALID_SORT_ATTRIBUTE,
        }
    )
    @validate_query_parameters(GetGroupUsersViewParamsSerializer)
    def get(self, request, group_id, query_params):
        """Responds with a list of serialized users that are part of the group."""

        search = query_params.get("search")
        sorts = query_params.get("sorts")

        group = CoreHandler().get_group(group_id)

        CoreHandler().check_permissions(
            request.user,
            ListGroupUsersGroupOperationType.type,
            group=group,
            context=group,
        )

        qs = GroupUser.objects.filter(group=group).select_related(
            "group", "user", "user__profile"
        )

        qs = self.apply_search(search, qs)
        qs = self.apply_sorts_or_default_sort(sorts, qs)

        serializer = ListGroupUsersWithMemberDataSerializer(qs, many=True)
        # Iterate over any registered `member_data_registry`
        # member data types and annotate the response with it.
        for data_type in member_data_registry.get_all():
            data_type.annotate_serialized_data(group, serializer.data)

        return Response(serializer.data)


class GroupUserView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_user_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the group user related to the provided value.",
            )
        ],
        tags=["Groups"],
        operation_id="update_group_user",
        description=(
            "Updates the existing group user related to the provided "
            "`group_user_id` param if the authorized user has admin rights to "
            "the related group."
        ),
        request=UpdateGroupUserSerializer,
        responses={
            200: GroupUserSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_USER_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(UpdateGroupUserSerializer)
    @map_exceptions(
        {
            GroupUserDoesNotExist: ERROR_GROUP_USER_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def patch(self, request, data, group_user_id):
        """Updates the group user if the user has admin permissions to the group."""

        group_user = CoreHandler().get_group_user(
            group_user_id,
            base_queryset=GroupUser.objects.select_for_update(of=("self",)),
        )
        group_user = CoreHandler().update_group_user(request.user, group_user, **data)
        return Response(GroupUserSerializer(group_user).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_user_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Deletes the group user related to the provided " "value.",
            )
        ],
        tags=["Groups"],
        operation_id="delete_group_user",
        description=(
            "Deletes a group user if the authorized user has admin rights to "
            "the related group."
        ),
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_USER_INVALID_GROUP_PERMISSIONS"]
            ),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            GroupUserDoesNotExist: ERROR_GROUP_USER_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
            CannotDeleteYourselfFromGroup: ERROR_CANNOT_DELETE_YOURSELF_FROM_GROUP,
        }
    )
    def delete(self, request, group_user_id):
        """Deletes an existing group_user if the user belongs to the group."""

        group_user = CoreHandler().get_group_user(
            group_user_id,
            base_queryset=GroupUser.objects.select_for_update(of=("self",)),
        )
        CoreHandler().delete_group_user(request.user, group_user)
        return Response(status=204)

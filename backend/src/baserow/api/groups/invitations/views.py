from django.db import transaction
from django.db.models import Exists, OuterRef
from django.contrib.auth import get_user_model

from itsdangerous.exc import BadSignature

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes

from baserow.api.decorators import validate_body, map_exceptions
from baserow.api.errors import (
    ERROR_USER_NOT_IN_GROUP,
    ERROR_USER_INVALID_GROUP_PERMISSIONS,
    ERROR_GROUP_DOES_NOT_EXIST,
    ERROR_HOSTNAME_IS_NOT_ALLOWED,
    BAD_TOKEN_SIGNATURE,
)
from baserow.api.schemas import get_error_schema
from baserow.api.groups.serializers import GroupUserGroupSerializer
from baserow.api.groups.users.errors import ERROR_GROUP_USER_ALREADY_EXISTS
from baserow.api.groups.invitations.errors import (
    ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
    ERROR_GROUP_INVITATION_EMAIL_MISMATCH,
)
from baserow.core.models import GroupInvitation
from baserow.core.handler import CoreHandler
from baserow.core.exceptions import (
    UserNotInGroup,
    UserInvalidGroupPermissionsError,
    GroupDoesNotExist,
    GroupInvitationDoesNotExist,
    BaseURLHostnameNotAllowed,
    GroupInvitationEmailMismatch,
    GroupUserAlreadyExists,
)

from .serializers import (
    GroupInvitationSerializer,
    CreateGroupInvitationSerializer,
    UpdateGroupInvitationSerializer,
    UserGroupInvitationSerializer,
)


User = get_user_model()


class GroupInvitationsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only invitations that are in the group related "
                "to the provided value.",
            )
        ],
        tags=["Group invitations"],
        operation_id="list_group_invitations",
        description=(
            "Lists all the group invitations of the group related to the provided "
            "`group_id` parameter if the authorized user has admin rights to that "
            "group."
        ),
        responses={
            200: GroupInvitationSerializer(many=True),
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_USER_INVALID_GROUP_PERMISSIONS"]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def get(self, request, group_id):
        """Lists all the invitations of the provided group id."""

        group = CoreHandler().get_group(group_id)
        group.has_user(request.user, "ADMIN", raise_error=True)
        group_invitations = GroupInvitation.objects.filter(group=group)
        serializer = GroupInvitationSerializer(group_invitations, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Creates a group invitation to the group related to the "
                "provided value.",
            )
        ],
        tags=["Group invitations"],
        operation_id="create_group_invitation",
        description=(
            "Creates a new group invitations for an email address if the authorized "
            "user has admin rights to the related group. An email containing a sign "
            "up link will be send to the user."
        ),
        request=CreateGroupInvitationSerializer,
        responses={
            200: GroupInvitationSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(CreateGroupInvitationSerializer)
    @map_exceptions(
        {
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
            GroupUserAlreadyExists: ERROR_GROUP_USER_ALREADY_EXISTS,
            BaseURLHostnameNotAllowed: ERROR_HOSTNAME_IS_NOT_ALLOWED,
        }
    )
    def post(self, request, data, group_id):
        """Creates a new group invitation and sends it the provided email."""

        group = CoreHandler().get_group(group_id)
        group_invitation = CoreHandler().create_group_invitation(
            request.user, group, **data
        )
        return Response(GroupInvitationSerializer(group_invitation).data)


class GroupInvitationView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_invitation_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the group invitation related to the provided "
                "value.",
            )
        ],
        tags=["Group invitations"],
        operation_id="get_group_invitation",
        description=(
            "Returns the requested group invitation if the authorized user has admin "
            "right to the related group"
        ),
        responses={
            200: GroupInvitationSerializer,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_USER_INVALID_GROUP_PERMISSIONS"]
            ),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            GroupInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def get(self, request, group_invitation_id):
        """Selects a single group invitation and responds with a serialized version."""

        group_invitation = CoreHandler().get_group_invitation(group_invitation_id)
        group_invitation.group.has_user(request.user, "ADMIN", raise_error=True)
        return Response(GroupInvitationSerializer(group_invitation).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_invitation_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the group invitation related to the provided "
                "value.",
            )
        ],
        tags=["Group invitations"],
        operation_id="update_group_invitation",
        description=(
            "Updates the existing group invitation related to the provided "
            "`group_invitation_id` param if the authorized user has admin rights to "
            "the related group."
        ),
        request=UpdateGroupInvitationSerializer,
        responses={
            200: GroupInvitationSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(UpdateGroupInvitationSerializer)
    @map_exceptions(
        {
            GroupInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def patch(self, request, data, group_invitation_id):
        """Updates the group invitation if the user belongs to the group."""

        group_invitation = CoreHandler().get_group_invitation(
            group_invitation_id,
            base_queryset=GroupInvitation.objects.select_for_update(),
        )
        group_invitation = CoreHandler().update_group_invitation(
            request.user, group_invitation, **data
        )
        return Response(GroupInvitationSerializer(group_invitation).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_invitation_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Deletes the group invitation related to the provided "
                "value.",
            )
        ],
        tags=["Group invitations"],
        operation_id="delete_group_invitation",
        description=(
            "Deletes a group invitation if the authorized user has admin rights to "
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
            GroupInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def delete(self, request, group_invitation_id):
        """Deletes an existing group_invitation if the user belongs to the group."""

        group_invitation = CoreHandler().get_group_invitation(
            group_invitation_id,
            base_queryset=GroupInvitation.objects.select_for_update(),
        )
        CoreHandler().delete_group_invitation(request.user, group_invitation)
        return Response(status=204)


class AcceptGroupInvitationView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_invitation_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Accepts the group invitation related to the provided "
                "value.",
            )
        ],
        tags=["Group invitations"],
        operation_id="accept_group_invitation",
        description=(
            "Accepts a group invitation with the given id if the email address of the "
            "user matches that of the invitation."
        ),
        request=None,
        responses={
            200: GroupUserGroupSerializer,
            400: get_error_schema(["ERROR_GROUP_INVITATION_EMAIL_MISMATCH"]),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            GroupInvitationEmailMismatch: ERROR_GROUP_INVITATION_EMAIL_MISMATCH,
            GroupInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
        }
    )
    def post(self, request, group_invitation_id):
        """Accepts a group invitation."""

        try:
            group_invitation = GroupInvitation.objects.select_related("group").get(
                id=group_invitation_id
            )
        except GroupInvitation.DoesNotExist:
            raise GroupInvitationDoesNotExist(
                f"The group invitation with id {group_invitation_id} does not exist."
            )

        group_user = CoreHandler().accept_group_invitation(
            request.user, group_invitation
        )
        return Response(GroupUserGroupSerializer(group_user).data)


class RejectGroupInvitationView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_invitation_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Rejects the group invitation related to the provided "
                "value.",
            )
        ],
        tags=["Group invitations"],
        operation_id="reject_group_invitation",
        description=(
            "Rejects a group invitation with the given id if the email address of the "
            "user matches that of the invitation."
        ),
        request=None,
        responses={
            204: None,
            400: get_error_schema(["ERROR_GROUP_INVITATION_EMAIL_MISMATCH"]),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            GroupInvitationEmailMismatch: ERROR_GROUP_INVITATION_EMAIL_MISMATCH,
            GroupInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
        }
    )
    def post(self, request, group_invitation_id):
        """Rejects a group invitation."""

        try:
            group_invitation = GroupInvitation.objects.select_related("group").get(
                id=group_invitation_id
            )
        except GroupInvitation.DoesNotExist:
            raise GroupInvitationDoesNotExist(
                f"The group invitation with id {group_invitation_id} does not exist."
            )

        CoreHandler().reject_group_invitation(request.user, group_invitation)
        return Response(status=204)


class GroupInvitationByTokenView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                description="Returns the group invitation related to the provided "
                "token.",
            )
        ],
        tags=["Group invitations"],
        operation_id="get_group_invitation_by_token",
        description=(
            "Responds with the serialized group invitation if an invitation with the "
            "provided token is found."
        ),
        responses={
            200: UserGroupInvitationSerializer,
            400: get_error_schema(["BAD_TOKEN_SIGNATURE"]),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            BadSignature: BAD_TOKEN_SIGNATURE,
            GroupInvitationDoesNotExist: ERROR_GROUP_INVITATION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, token):
        """
        Responds with the serialized group invitation if an invitation with the
        provided token is found.
        """

        exists_queryset = User.objects.filter(username=OuterRef("email"))
        group_invitation = CoreHandler().get_group_invitation_by_token(
            token,
            base_queryset=GroupInvitation.objects.annotate(
                email_exists=Exists(exists_queryset)
            ),
        )
        return Response(UserGroupInvitationSerializer(group_invitation).data)

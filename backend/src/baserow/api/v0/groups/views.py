from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from baserow.api.v0.decorators import validate_body, map_exceptions
from baserow.api.v0.errors import ERROR_USER_NOT_IN_GROUP
from baserow.core.models import Group, GroupUser
from baserow.core.handler import CoreHandler
from baserow.core.exceptions import UserNotInGroupError

from .serializers import GroupSerializer, GroupUserSerializer, OrderGroupsSerializer


class GroupsView(APIView):
    permission_classes = (IsAuthenticated,)
    core_handler = CoreHandler()

    def get(self, request):
        """Responds with a list of groups where the users takes part in."""

        groups = GroupUser.objects.filter(user=request.user).select_related('group')
        serializer = GroupUserSerializer(groups, many=True)
        return Response(serializer.data)

    @transaction.atomic
    @validate_body(GroupSerializer)
    def post(self, request, data):
        """Creates a new group for a user."""

        group_user = self.core_handler.create_group(request.user, name=data['name'])
        return Response(GroupUserSerializer(group_user).data)


class GroupView(APIView):
    permission_classes = (IsAuthenticated,)
    core_handler = CoreHandler()

    @staticmethod
    def get_group_user(user, group_id):
        try:
            group_user = GroupUser.objects.select_related('group') \
                .select_for_update().get(group_id=group_id, user=user)
        except GroupUser.DoesNotExist:
            # If the group user doesn't exist we should check if the group exist so we
            # can show a proper error.
            get_object_or_404(Group, id=group_id)
            raise UserNotInGroupError

        return group_user

    @transaction.atomic
    @validate_body(GroupSerializer)
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def patch(self, request, data, group_id):
        """Updates the group if it belongs to a user."""

        group_user = self.get_group_user(request.user, group_id)
        group_user.group = self.core_handler.update_group(
            request.user,  group_user.group, name=data['name'])

        return Response(GroupUserSerializer(group_user).data)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def delete(self, request, group_id):
        """Deletes an existing group if it belongs to a user."""

        group_user = self.get_group_user(request.user, group_id)
        self.core_handler.delete_group(request.user,  group_user.group)
        return Response(status=204)


class GroupOrderView(APIView):
    permission_classes = (IsAuthenticated,)
    core_handler = CoreHandler()

    @validate_body(OrderGroupsSerializer)
    def post(self, request, data):
        """Updates to order of some groups for a user."""

        self.core_handler.order_groups(request.user, data['groups'])
        return Response(status=204)

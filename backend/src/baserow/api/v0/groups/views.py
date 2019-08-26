from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from baserow.core.models import GroupUser
from baserow.core.handler import CoreHandler

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
    def post(self, request):
        """Creates a new group for a user."""
        serializer = GroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.data
        group_user = self.core_handler.create_group(request.user, name=data['name'])

        return Response(GroupUserSerializer(group_user).data)


class GroupView(APIView):
    permission_classes = (IsAuthenticated,)
    core_handler = CoreHandler()

    @transaction.atomic
    def patch(self, request, group_id):
        """Updates the group if it belongs to a user."""
        group_user = get_object_or_404(GroupUser, group_id=group_id, user=request.user)

        serializer = GroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.data
        group_user.group = self.core_handler.update_group(
            request.user,  group_user.group, name=data['name'])

        return Response(GroupUserSerializer(group_user).data)

    @transaction.atomic
    def delete(self, request, group_id):
        """Deletes an existing group if it belongs to a user."""
        group_user = get_object_or_404(GroupUser, group_id=group_id, user=request.user)
        self.core_handler.delete_group(request.user,  group_user.group)
        return Response(status=204)


class GroupOrderView(APIView):
    permission_classes = (IsAuthenticated,)
    core_handler = CoreHandler()

    def post(self, request):
        """Updates to order of some groups for a user."""
        serializer = OrderGroupsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.core_handler.order_groups(request.user, serializer.data['groups'])

        return Response(status=204)

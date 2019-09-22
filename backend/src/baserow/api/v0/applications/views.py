from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from baserow.api.v0.decorators import validate_body, map_exceptions
from baserow.core.models import GroupUser, Application
from baserow.core.handler import CoreHandler
from baserow.core.exceptions import UserNotIngroupError

from .serializers import (
    ApplicationSerializer, ApplicationCreateSerializer, ApplicationUpdateSerializer
)
from .errors import ERROR_USER_NOT_IN_GROUP


class ApplicationsView(APIView):
    permission_classes = (IsAuthenticated,)
    core_handler = CoreHandler()

    def load_group(self, request, group_id):
        return get_object_or_404(
            GroupUser.objects.select_related('group'),
            group_id=group_id,
            user=request.user
        )

    def get(self, request, group_id):
        """
        Responds with a list of applications that belong to the group if the user has
        access to that group.
        """

        group_user = self.load_group(request, group_id)
        applications = Application.objects.filter(
            group=group_user.group
        ).select_related('content_type')
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data)

    @transaction.atomic
    @validate_body(ApplicationCreateSerializer)
    def post(self, request, data, group_id):
        """Creates a new application for a user."""

        group_user = self.load_group(request, group_id)
        application = self.core_handler.create_application(
            request.user, group_user.group, data['type'], name=data['name'])

        return Response(ApplicationSerializer(application).data)


class ApplicationView(APIView):
    permission_classes = (IsAuthenticated,)
    core_handler = CoreHandler()

    @transaction.atomic
    @validate_body(ApplicationUpdateSerializer)
    @map_exceptions({
        UserNotIngroupError: ERROR_USER_NOT_IN_GROUP
    })
    def patch(self, request, data, application_id):
        """Updates the application if the user belongs to the group."""

        application = get_object_or_404(
            Application.objects.select_related('group').select_for_update(),
            pk=application_id
        )
        application = self.core_handler.update_application(
            request.user, application, name=data['name'])

        return Response(ApplicationSerializer(application).data)

    @transaction.atomic
    @map_exceptions({
        UserNotIngroupError: ERROR_USER_NOT_IN_GROUP
    })
    def delete(self, request, application_id):
        """Deletes an existing application if the user belongs to the group."""

        application = get_object_or_404(
            Application.objects.select_related('group'),
            pk=application_id
        )
        self.core_handler.delete_application(request.user, application)

        return Response(status=204)

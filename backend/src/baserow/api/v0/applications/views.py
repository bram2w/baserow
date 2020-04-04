from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from baserow.api.v0.decorators import validate_body, map_exceptions
from baserow.api.v0.errors import ERROR_USER_NOT_IN_GROUP
from baserow.core.models import Group, Application
from baserow.core.handler import CoreHandler
from baserow.core.exceptions import UserNotInGroupError

from .serializers import (
    ApplicationCreateSerializer, ApplicationUpdateSerializer, get_application_serializer
)


class ApplicationsView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get_group(request, group_id):
        group = get_object_or_404(
            Group,
            id=group_id
        )

        if not group.has_user(request.user):
            raise UserNotInGroupError(request.user, group)

        return group

    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, group_id=None):
        """
        Responds with a list of serialized applications that belong to the user. If a
        group id is provided only the applications of that group are going to be
        returned.
        """

        applications = Application.objects.select_related('content_type')

        if group_id:
            group = self.get_group(request, group_id)
            applications = applications.filter(group=group)
        else:
            applications = applications.filter(group__users__in=[request.user])

        data = [
            get_application_serializer(application).data
            for application in applications
        ]
        return Response(data)

    @transaction.atomic
    @validate_body(ApplicationCreateSerializer)
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def post(self, request, data, group_id):
        """Creates a new application for a user."""

        group = self.get_group(request, group_id)
        application = CoreHandler().create_application(
            request.user, group, data['type'], name=data['name'])

        return Response(get_application_serializer(application).data)


class ApplicationView(APIView):
    permission_classes = (IsAuthenticated,)

    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, application_id):
        """Selects a single application and responds with a serialized version."""

        application = get_object_or_404(
            Application.objects.select_related('group'),
            pk=application_id
        )

        if not application.group.has_user(request.user):
            raise UserNotInGroupError(request.user, application.group)

        return Response(get_application_serializer(application).data)

    @transaction.atomic
    @validate_body(ApplicationUpdateSerializer)
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def patch(self, request, data, application_id):
        """Updates the application if the user belongs to the group."""

        application = get_object_or_404(
            Application.objects.select_related('group').select_for_update(),
            pk=application_id
        )
        application = CoreHandler().update_application(
            request.user, application, name=data['name'])

        return Response(get_application_serializer(application).data)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def delete(self, request, application_id):
        """Deletes an existing application if the user belongs to the group."""

        application = get_object_or_404(
            Application.objects.select_related('group'),
            pk=application_id
        )
        CoreHandler().delete_application(request.user, application)

        return Response(status=204)

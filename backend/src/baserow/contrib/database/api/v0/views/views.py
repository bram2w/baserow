from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from baserow.api.v0.decorators import validate_body_custom_fields, map_exceptions
from baserow.api.v0.utils import validate_data_custom_fields
from baserow.api.v0.errors import ERROR_USER_NOT_IN_GROUP
from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.registries import view_type_registry
from baserow.contrib.database.views.models import View
from baserow.contrib.database.views.handler import ViewHandler

from .serializers import ViewSerializer, CreateViewSerializer, UpdateViewSerializer


class ViewsView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get_table(user, table_id):
        table = get_object_or_404(
            Table.objects.select_related('database__group'),
            id=table_id
        )

        group = table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        return table

    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, table_id):
        """
        Responds with a list of serialized views that belong to the table if the user
        has access to that group.
        """

        table = self.get_table(request.user, table_id)
        views = View.objects.filter(table=table).select_related('content_type')
        data = [
            view_type_registry.get_serializer(view, ViewSerializer).data
            for view in views
        ]
        return Response(data)

    @transaction.atomic
    @validate_body_custom_fields(
        view_type_registry, base_serializer_class=CreateViewSerializer)
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def post(self, request, data, table_id):
        """Creates a new view for a user."""

        table = self.get_table(request.user, table_id)
        view = ViewHandler().create_view(
            request.user, table, data.pop('type'), **data)

        serializer = view_type_registry.get_serializer(view, ViewSerializer)
        return Response(serializer.data)


class ViewView(APIView):
    permission_classes = (IsAuthenticated,)

    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, view_id):
        """Selects a single view and responds with a serialized version."""

        view = get_object_or_404(
            View.objects.select_related('table__database__group'),
            pk=view_id
        )

        group = view.table.database.group
        if not group.has_user(request.user):
            raise UserNotInGroupError(request.user, group)

        serializer = view_type_registry.get_serializer(view, ViewSerializer)
        return Response(serializer.data)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def patch(self, request, view_id):
        """Updates the view if the user belongs to the group."""

        view = get_object_or_404(
            View.objects.select_related('table__database__group').select_for_update(),
            pk=view_id
        ).specific

        view_type = view_type_registry.get_by_model(view)
        data = validate_data_custom_fields(
            view_type.type, view_type_registry, request.data,
            base_serializer_class=UpdateViewSerializer
        )

        view = ViewHandler().update_view(request.user, view, **data)

        serializer = view_type_registry.get_serializer(view, ViewSerializer)
        return Response(serializer.data)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def delete(self, request, view_id):
        """Deletes an existing view if the user belongs to the group."""

        view = get_object_or_404(
            View.objects.select_related('table__database__group'),
            pk=view_id
        )
        ViewHandler().delete_view(request.user, view)

        return Response(status=204)

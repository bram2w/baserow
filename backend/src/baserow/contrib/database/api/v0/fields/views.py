from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from baserow.api.v0.decorators import validate_body_custom_fields, map_exceptions
from baserow.api.v0.utils import validate_data_custom_fields, type_from_data_or_registry
from baserow.api.v0.errors import ERROR_USER_NOT_IN_GROUP
from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.api.v0.fields.errors import (
    ERROR_CANNOT_DELETE_PRIMARY_FIELD, ERROR_CANNOT_CHANGE_FIELD_TYPE
)
from baserow.contrib.database.fields.exceptions import (
    CannotDeletePrimaryField, CannotChangeFieldType
)
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.registries import field_type_registry

from .serializers import (
    FieldSerializer, CreateFieldSerializer, UpdateFieldSerializer
)


class FieldsView(APIView):
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
        Responds with a list of serialized fields that belong to the table if the user
        has access to that group.
        """

        table = self.get_table(request.user, table_id)
        fields = Field.objects.filter(table=table).select_related('content_type')

        data = [
            field_type_registry.get_serializer(field, FieldSerializer).data
            for field in fields
        ]
        return Response(data)

    @transaction.atomic
    @validate_body_custom_fields(
        field_type_registry, base_serializer_class=CreateFieldSerializer)
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def post(self, request, data, table_id):
        """Creates a new field for a table."""

        type_name = data.pop('type')
        table = self.get_table(request.user, table_id)
        field = FieldHandler().create_field(
            request.user, table, type_name, **data)

        serializer = field_type_registry.get_serializer(field, FieldSerializer)
        return Response(serializer.data)


class FieldView(APIView):
    permission_classes = (IsAuthenticated,)

    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP
    })
    def get(self, request, field_id):
        """Selects a single field and responds with a serialized version."""

        field = get_object_or_404(
            Field.objects.select_related('table__database__group'),
            pk=field_id
        )

        group = field.table.database.group
        if not group.has_user(request.user):
            raise UserNotInGroupError(request.user, group)

        serializer = field_type_registry.get_serializer(field, FieldSerializer)
        return Response(serializer.data)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        CannotChangeFieldType: ERROR_CANNOT_CHANGE_FIELD_TYPE
    })
    def patch(self, request, field_id):
        """Updates the field if the user belongs to the group."""

        field = get_object_or_404(
            Field.objects.select_related('table__database__group').select_for_update(),
            pk=field_id
        ).specific

        type_name = type_from_data_or_registry(request.data, field_type_registry, field)
        data = validate_data_custom_fields(type_name, field_type_registry, request.data,
                                           base_serializer_class=UpdateFieldSerializer)

        field = FieldHandler().update_field(request.user, field, type_name, **data)

        serializer = field_type_registry.get_serializer(field, FieldSerializer)
        return Response(serializer.data)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        CannotDeletePrimaryField: ERROR_CANNOT_DELETE_PRIMARY_FIELD
    })
    def delete(self, request, field_id):
        """Deletes an existing field if the user belongs to the group."""

        field = get_object_or_404(
            Field.objects.select_related('table__database__group'),
            pk=field_id
        )
        FieldHandler().delete_field(request.user, field)

        return Response(status=204)

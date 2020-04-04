from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from baserow.api.v0.utils import validate_data
from baserow.api.v0.decorators import map_exceptions
from baserow.api.v0.errors import ERROR_USER_NOT_IN_GROUP
from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.api.v0.tables.errors import ERROR_TABLE_DOES_NOT_EXIST
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.api.v0.rows.errors import ERROR_ROW_DOES_NOT_EXIST
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.rows.exceptions import RowDoesNotExist

from .serializers import RowSerializer, get_row_serializer_class


class RowsView(APIView):
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST
    })
    def post(self, request, table_id):
        """
        Creates a new row for the given table_id. Also the post data is validated
        according to the tables field types.
        """

        table = TableHandler().get_table(request.user, table_id)
        model = table.get_model()

        validation_serializer = get_row_serializer_class(model)
        data = validate_data(validation_serializer, request.data)

        row = RowHandler().create_row(request.user, table, data, model)
        serializer_class = get_row_serializer_class(model, RowSerializer)
        serializer = serializer_class(row)

        return Response(serializer.data)


class RowView(APIView):
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
        RowDoesNotExist: ERROR_ROW_DOES_NOT_EXIST
    })
    def patch(self, request, table_id, row_id):
        """
        Updates the row with the given row_id for the table with the given
        table_id. Also the post data is validated according to the tables field types.
        """

        table = TableHandler().get_table(request.user, table_id)

        # Small side effect of generating the model for only the fields that need to
        # change is that the response it not going to contain the other fields. It is
        # however much faster because it doesn't need to get the specific version of
        # all the field objects.
        field_ids = RowHandler().extract_field_ids_from_dict(request.data)
        model = table.get_model(field_ids=field_ids)

        validation_serializer = get_row_serializer_class(model)
        data = validate_data(validation_serializer, request.data)

        row = RowHandler().update_row(request.user, table, row_id, data, model)

        serializer_class = get_row_serializer_class(model, RowSerializer)
        serializer = serializer_class(row)

        return Response(serializer.data)

    @transaction.atomic
    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
        RowDoesNotExist: ERROR_ROW_DOES_NOT_EXIST
    })
    def delete(self, request, table_id, row_id):
        """
        Deletes an existing row with the given row_id for table with the given table_id.
        """

        table = TableHandler().get_table(request.user, table_id)
        RowHandler().delete_row(request.user, table, row_id)

        return Response(status=204)

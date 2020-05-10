from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination

from baserow.api.v0.decorators import map_exceptions, allowed_includes, validate_body
from baserow.api.v0.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.v0.pagination import PageNumberPagination
from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.api.v0.rows.serializers import (
    get_row_serializer_class, RowSerializer
)
from baserow.contrib.database.api.v0.views.grid.serializers import GridViewSerializer
from baserow.contrib.database.views.exceptions import (
    ViewDoesNotExist, UnrelatedFieldError
)
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import GridView

from .errors import ERROR_GRID_DOES_NOT_EXIST, ERROR_UNRELATED_FIELD


class GridViewView(APIView):
    permission_classes = (IsAuthenticated,)

    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        ViewDoesNotExist: ERROR_GRID_DOES_NOT_EXIST
    })
    @allowed_includes('field_options')
    def get(self, request, view_id, field_options):
        """
        Lists all the rows of a grid view, paginated either by a page or offset/limit.
        If the limit get parameter is provided the limit/offset pagination will be used
        else the page number pagination.

        Optionally the field options can also be included in the response if the the
        `field_options` are provided in the includes GET parameter.
        """

        view = ViewHandler().get_view(request.user, view_id, GridView)

        model = view.table.get_model()
        queryset = model.objects.all().order_by('id')

        if LimitOffsetPagination.limit_query_param in request.GET:
            paginator = LimitOffsetPagination()
        else:
            paginator = PageNumberPagination()

        page = paginator.paginate_queryset(queryset, request, self)
        serializer_class = get_row_serializer_class(model, RowSerializer)
        serializer = serializer_class(page, many=True)

        response = paginator.get_paginated_response(serializer.data)

        if field_options:
            # The serializer has the GridViewFieldOptionsField which fetches the
            # field options from the database and creates them if they don't exist,
            # but when added to the context the fields don't have to be fetched from
            # the database again when checking if they exist.
            context = {'fields': [o['field'] for o in model._field_objects.values()]}
            response.data.update(**GridViewSerializer(view, context=context).data)

        return response

    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        ViewDoesNotExist: ERROR_GRID_DOES_NOT_EXIST,
        UnrelatedFieldError: ERROR_UNRELATED_FIELD
    })
    @validate_body(GridViewSerializer)
    def patch(self, request, view_id, data):
        """
        Updates the field options for the provided grid view.

        The following example body data will only update the width of the FIELD_ID
        and leaves the others untouched.
            {
                FIELD_ID: {
                    'width': 200
                }
            }
        """

        handler = ViewHandler()
        view = handler.get_view(request.user, view_id, GridView)
        handler.update_grid_view_field_options(view, data['field_options'])
        return Response(GridViewSerializer(view).data)

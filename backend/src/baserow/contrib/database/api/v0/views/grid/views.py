from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination

from baserow.api.v0.decorators import map_exceptions
from baserow.api.v0.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.v0.pagination import PageNumberPagination
from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.api.v0.rows.serializers import (
    get_row_serializer_class, RowSerializer
)
from baserow.contrib.database.views.exceptions import ViewDoesNotExist
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import GridView

from .errors import ERROR_GRID_DOES_NOT_EXIST


class GridViewView(APIView):
    permission_classes = (IsAuthenticated,)

    @map_exceptions({
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        ViewDoesNotExist: ERROR_GRID_DOES_NOT_EXIST
    })
    def get(self, request, view_id):
        """
        Lists all the rows of a grid view, paginated either by a page or offset/limit.
        If the limit get parameter is provided the limit/offset pagination will be used
        else the page number pagination.
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

        return paginator.get_paginated_response(serializer.data)

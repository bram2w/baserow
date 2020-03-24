from rest_framework.exceptions import NotFound, APIException
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.pagination import (
    PageNumberPagination as RestFrameworkPageNumberPagination
)


class PageNumberPagination(RestFrameworkPageNumberPagination):
    page_size = 100
    page_size_query_param = 'size'

    def paginate_queryset(self, *args, **kwargs):
        """Adds a machine readable error code if the page is not found."""

        try:
            return super().paginate_queryset(*args, **kwargs)
        except NotFound as e:
            exception = APIException({
                'error': 'ERROR_INVALID_PAGE',
                'detail': str(e)
            })
            exception.status_code = HTTP_400_BAD_REQUEST
            raise exception

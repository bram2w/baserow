from rest_framework.exceptions import NotFound, APIException
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.pagination import (
    PageNumberPagination as RestFrameworkPageNumberPagination,
)


class PageNumberPagination(RestFrameworkPageNumberPagination):
    # Please keep the default page size in sync with the default prop pageSize in
    # web-frontend/modules/core/components/helpers/InfiniteScroll.vue
    page_size = 100
    page_size_query_param = "size"

    def __init__(self, limit_page_size=None, *args, **kwargs):
        self.limit_page_size = limit_page_size
        super().__init__(*args, **kwargs)

    def get_page_size(self, request):
        page_size = super().get_page_size(request)

        if self.limit_page_size and page_size > self.limit_page_size:
            exception = APIException(
                {
                    "error": "ERROR_PAGE_SIZE_LIMIT",
                    "detail": f"The page size is limited to {self.limit_page_size}.",
                }
            )
            exception.status_code = HTTP_400_BAD_REQUEST
            raise exception

        return page_size

    def paginate_queryset(self, *args, **kwargs):
        """Adds a machine readable error code if the page is not found."""

        try:
            return super().paginate_queryset(*args, **kwargs)
        except NotFound as e:
            exception = APIException({"error": "ERROR_INVALID_PAGE", "detail": str(e)})
            exception.status_code = HTTP_400_BAD_REQUEST
            raise exception

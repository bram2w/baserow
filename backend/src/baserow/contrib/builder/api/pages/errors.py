from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_PAGE_DOES_NOT_EXIST = (
    "ERROR_PAGE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested page does not exist.",
)

ERROR_PAGE_NOT_IN_BUILDER = (
    "ERROR_PAGE_NOT_IN_BUILDER",
    HTTP_400_BAD_REQUEST,
    "The page id {e.page_id} does not belong to the builder.",
)

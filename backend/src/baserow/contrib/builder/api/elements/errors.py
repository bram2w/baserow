from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_ELEMENT_DOES_NOT_EXIST = (
    "ERROR_ELEMENT_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested element does not exist.",
)

ERROR_ELEMENT_NOT_IN_PAGE = (
    "ERROR_ELEMENT_NOT_IN_PAGE",
    HTTP_400_BAD_REQUEST,
    "The element id {e.element_id} does not belong to the page.",
)

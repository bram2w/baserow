from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_TEMPLATE_DOES_NOT_EXIST = (
    "ERROR_TEMPLATE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested template does not exist.",
)
ERROR_TEMPLATE_FILE_DOES_NOT_EXIST = (
    "ERROR_TEMPLATE_FILE_DOES_NOT_EXIST",
    HTTP_400_BAD_REQUEST,
    "The requested template file does not exist anymore.",
)

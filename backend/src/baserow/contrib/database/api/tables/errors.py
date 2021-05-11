from django.conf import settings

from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND


ERROR_TABLE_DOES_NOT_EXIST = (
    "ERROR_TABLE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested table does not exist.",
)
ERROR_INVALID_INITIAL_TABLE_DATA = (
    "ERROR_INVALID_INITIAL_TABLE_DATA",
    HTTP_400_BAD_REQUEST,
    "The provided table data must at least contain one row and one column.",
)
ERROR_TABLE_DOES_NOT_BELONG_TO_GROUP = (
    "ERROR_TABLE_DOES_NOT_BELONG_TO_GROUP",
    HTTP_400_BAD_REQUEST,
    "The provided table does not belong to the related group.",
)
ERROR_INITIAL_TABLE_DATA_LIMIT_EXCEEDED = (
    "ERROR_INITIAL_TABLE_DATA_LIMIT_EXCEEDED",
    HTTP_400_BAD_REQUEST,
    f"The initial table data limit has been exceeded. You can provide a maximum of "
    f"{settings.INITIAL_TABLE_DATA_LIMIT} rows.",
)

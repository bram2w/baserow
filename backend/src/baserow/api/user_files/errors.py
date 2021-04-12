from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
)


ERROR_INVALID_FILE = (
    "ERROR_INVALID_FILE",
    HTTP_400_BAD_REQUEST,
    "No file has been provided or the file is invalid.",
)
ERROR_FILE_SIZE_TOO_LARGE = (
    "ERROR_FILE_SIZE_TOO_LARGE",
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    "The provided file is too large. Max {e.max_size_mb}MB is allowed.",
)
ERROR_FILE_URL_COULD_NOT_BE_REACHED = (
    "ERROR_FILE_URL_COULD_NOT_BE_REACHED",
    HTTP_400_BAD_REQUEST,
    "The provided URL could not be reached.",
)
ERROR_INVALID_FILE_URL = (
    "ERROR_INVALID_FILE_URL",
    HTTP_400_BAD_REQUEST,
    "The provided URL is not valid.",
)
ERROR_INVALID_USER_FILE_NAME_ERROR = (
    "ERROR_INVALID_USER_FILE_NAME_ERROR",
    HTTP_400_BAD_REQUEST,
    "The user file name {e.name} is invalid.",
)
ERROR_USER_FILE_DOES_NOT_EXIST = (
    "ERROR_USER_FILE_DOES_NOT_EXIST",
    HTTP_400_BAD_REQUEST,
    "The user file {e.name_or_id} does not exist.",
)

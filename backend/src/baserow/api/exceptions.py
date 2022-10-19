from django.conf import settings

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError


class RequestBodyValidationException(APIException):
    def __init__(self, detail=None, code=None):
        super().__init__(
            {"error": "ERROR_REQUEST_BODY_VALIDATION", "detail": detail}, code=code
        )
        self.status_code = 400


class UnknownFieldProvided(ValidationError):
    """
    Raised when an unknown field is provided to an API endpoint.
    """


class QueryParameterValidationException(APIException):
    def __init__(self, detail=None, code=None):
        super().__init__(
            {"error": "ERROR_QUERY_PARAMETER_VALIDATION", "detail": detail}, code=code
        )
        self.status_code = 400


class InvalidClientSessionIdAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "ERROR_INVALID_CLIENT_SESSION_ID"
    default_detail = (
        f"An invalid {settings.CLIENT_SESSION_ID_HEADER} header was provided. It must "
        f"be between 1 and {settings.MAX_CLIENT_SESSION_ID_LENGTH} characters long and "
        f"must only contain alphanumeric or the - characters.",
    )


class InvalidUndoRedoActionGroupIdAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "ERROR_INVALID_CLIENT_ACTION_GROUP"
    default_detail = (
        f"An invalid {settings.CLIENT_UNDO_REDO_ACTION_GROUP_ID_HEADER} header was provided. "
        f"It must be a valid Version 4 UUID.",
    )


class InvalidSortDirectionException(Exception):
    """
    Raised when an invalid sort direction is provided.
    """


class InvalidSortAttributeException(Exception):
    """
    Raised when a sort is requested for an invalid or non-existent field.
    """

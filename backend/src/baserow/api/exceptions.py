from rest_framework.exceptions import APIException


class RequestBodyValidationException(APIException):
    def __init__(self, detail=None, code=None):
        super().__init__(
            {"error": "ERROR_REQUEST_BODY_VALIDATION", "detail": detail}, code=code
        )
        self.status_code = 400


class UnknownFieldProvided(Exception):
    """
    Raised when an unknown field is provided to an API endpoint.
    """


class QueryParameterValidationException(APIException):
    def __init__(self, detail=None, code=None):
        super().__init__(
            {"error": "ERROR_QUERY_PARAMETER_VALIDATION", "detail": detail}, code=code
        )
        self.status_code = 400

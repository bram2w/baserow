from rest_framework.exceptions import APIException


class FiltersParamValidationException(APIException):
    def __init__(self, detail=None, code=None):
        super().__init__(
            {"error": "ERROR_FILTERS_PARAM_VALIDATION_ERROR", "detail": detail},
            code=code,
        )
        self.status_code = 400

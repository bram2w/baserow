from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_402_PAYMENT_REQUIRED


class SingleSignOnFeatureNotAvailableError(APIException):
    """
    Raised when the single-sign-on feature is not available for this Baserow instance.
    """

    def __init__(self):
        super().__init__(
            {
                "error": "ERROR_NO_SINGLE_SIGN_ON_FEATURE_AVAILABLE",
                "detail": "The single-sign-on feature is not enabled for this Baserow instance.",
            },
            code=HTTP_402_PAYMENT_REQUIRED,
        )
        self.status_code = HTTP_402_PAYMENT_REQUIRED

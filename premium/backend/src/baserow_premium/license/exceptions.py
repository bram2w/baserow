from rest_framework.status import HTTP_402_PAYMENT_REQUIRED
from rest_framework.exceptions import APIException


class NoPremiumLicenseError(APIException):
    """
    Raised when the related user does not have an active license for the premium
    version.
    """

    def __init__(self):
        super().__init__(
            {
                "error": "ERROR_NO_ACTIVE_PREMIUM_LICENSE",
                "detail": "The related user does not have access to the premium "
                "version.",
            },
            code=HTTP_402_PAYMENT_REQUIRED,
        )
        self.status_code = HTTP_402_PAYMENT_REQUIRED


class InvalidPremiumLicenseError(Exception):
    """
    Raised when a provided premium license is not valid. This could be because the
    signature is incorrect or the payload does not contain the required information.
    """


class UnsupportedPremiumLicenseError(Exception):
    """
    Raised when the version of the license is not supported. This probably means that
    Baserow must be upgraded.
    """


class PremiumLicenseInstanceIdMismatchError(Exception):
    """
    Raised when trying to register a license and the instance ids of the license and
    self hosted copy don't match.
    """


class PremiumLicenseAlreadyExists(Exception):
    """Raised when trying to register a license that already exists."""


class PremiumLicenseHasExpired(Exception):
    """Raised when trying to register a license that is expired."""


class UserAlreadyOnPremiumLicenseError(Exception):
    """Raised when the user already has a seat in the license."""


class NoSeatsLeftInPremiumLicenseError(Exception):
    """Raised when there are no seats left in the license."""


class LicenseAuthorityUnavailable(Exception):
    """Raised when the license authority can't be reached."""

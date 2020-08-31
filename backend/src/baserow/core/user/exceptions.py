class UserNotFound(Exception):
    """Raised when a user with given parameters is not found."""


class UserAlreadyExist(Exception):
    """Raised when a user could not be created because the email already exists."""


class InvalidPassword(Exception):
    """Raised when the provided password is incorrect."""


class BaseURLDomainNotAllowed(Exception):
    """
    Raised when the provided base url is not allowed when requesting a password
    reset email.
    """

class UserNotFound(Exception):
    """Raised when a user with given parameters is not found."""


class UserAlreadyExist(Exception):
    """Raised when a user could not be created because the email already exists."""

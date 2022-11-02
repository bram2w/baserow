class UserNotFound(Exception):
    """Raised when a user with given parameters is not found."""


class UserAlreadyExist(Exception):
    """Raised when a user could not be created because the email already exists."""


class PasswordDoesNotMatchValidation(Exception):
    """Raised when the provided password does not match validation."""


class InvalidPassword(Exception):
    """Raised when the provided password is incorrect."""


class UserIsLastAdmin(Exception):
    """
    Raised when a user wants to delete himself but is the last instance wide admin.
    """


class DisabledSignupError(Exception):
    """
    Raised when a user account is created when the new signup setting is disabled.
    """


class ResetPasswordDisabledError(Exception):
    """Raised when a password reset is attempted but the password reset is disabled."""


class DeactivatedUserException(Exception):
    pass

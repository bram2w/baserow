class DifferentAuthProvider(Exception):
    """
    Raised when logging in an existing user that should not
    be logged in using a different than the approved auth provider.
    """


class CannotCreateAuthProvider(Exception):
    """
    Raised when a provider type cannot be created.
    """


class CannotDeleteAuthProvider(Exception):
    """
    Raised when a provider type cannot be deleted.
    """


class CannotDisableLastAuthProvider(Exception):
    """
    Raised during an attempt to disable last enabled auth provider.
    """

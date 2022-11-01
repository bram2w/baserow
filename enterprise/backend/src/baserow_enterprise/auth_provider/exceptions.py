class DifferentAuthProvider(Exception):
    """
    Raised when logging in an existing user that should not
    be logged in using a different than the approved auth provider.
    """

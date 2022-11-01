class AuthProviderDoesNotExist(Exception):
    """
    Raised when a requested auth provider doesn't exist.
    """


class InvalidProviderUrl(Exception):
    """
    Specified auth provider doesn't exist on this URL or doesn't work.
    """


class AuthFlowError(Exception):
    """
    Error occured during the auth flow.
    """

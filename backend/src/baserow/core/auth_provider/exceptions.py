class AuthProviderModelNotFound(Exception):
    """Raised if the requested authentication provider does not exist."""


class AuthProviderDisabled(Exception):
    """Raised when it is not possible to use a particular auth provider."""

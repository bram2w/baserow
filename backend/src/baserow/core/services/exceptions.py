class ServiceDoesNotExist(Exception):
    """Raised when trying to get a service that doesn't exist."""


class ServiceImproperlyConfigured(Exception):
    """Raised when trying to dispatch a service that is not fully configured."""


class DoesNotExist(Exception):
    """Raised when calling a service dispatch method and nothing is found."""

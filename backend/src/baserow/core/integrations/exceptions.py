class IntegrationDoesNotExist(Exception):
    """Raised when trying to get an integration that doesn't exist."""


class IntegrationNotInSameApplication(Exception):
    """
    Raised when trying to order integrations that that don't belong to the same
    application.
    """

class TableWebhookDoesNotExist(Exception):
    """Raised when trying to fetch a webhook that does not exist."""


class TableWebhookMaxAllowedCountExceeded(Exception):
    """Raised when trying to create more webhooks than a table allows."""

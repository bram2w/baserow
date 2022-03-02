class AirtableBaseNotPublic(Exception):
    """Raised when the Airtable base is not publicly shared."""


class AirtableImportJobDoesNotExist(Exception):
    """Raised when the Airtable import job does not exist."""


class AirtableImportJobAlreadyRunning(Exception):
    """Raised when a user starts another import job while one is already running."""

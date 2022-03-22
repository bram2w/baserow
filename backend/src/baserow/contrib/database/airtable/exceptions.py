class AirtableBaseNotPublic(Exception):
    """Raised when the Airtable base is not publicly shared."""


class AirtableShareIsNotABase(Exception):
    """Raised when shared Airtable link is not a base."""


class AirtableImportJobDoesNotExist(Exception):
    """Raised when the Airtable import job does not exist."""


class AirtableImportJobAlreadyRunning(Exception):
    """Raised when a user starts another import job while one is already running."""

class AirtableBaseNotPublic(Exception):
    """Raised when the Airtable base is not publicly shared."""


class AirtableShareIsNotABase(Exception):
    """Raised when shared Airtable link is not a base."""

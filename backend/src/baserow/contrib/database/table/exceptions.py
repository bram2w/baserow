class TableDoesNotExist(Exception):
    """Raised when trying to get a table that doesn't exist."""


class InvalidInitialTableData(Exception):
    """Raised when the provided initial table data does not contain a column or row."""

class TableDoesNotExist(Exception):
    """Raised when trying to get a table that doesn't exist."""


class InvalidInitialTableData(Exception):
    """Raised when the provided initial table data does not contain a column or row."""


class TableDoesNotBelongToGroup(Exception):
    """Raised when the table does not belong to the related group."""


class InitialTableDataLimitExceeded(Exception):
    """
    Raised when the initial table data limit has been exceeded when creating a new
    table.
    """

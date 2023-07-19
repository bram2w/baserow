class DataSourceDoesNotExist(Exception):
    """Raised when trying to get an data_source that doesn't exist."""


class DataSourceNotInSamePage(Exception):
    """
    Raised when trying to move a data_source before a data_source on a different
    page.
    """

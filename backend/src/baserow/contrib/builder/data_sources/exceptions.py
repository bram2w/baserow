class DataSourceDoesNotExist(Exception):
    """Raised when trying to get a data_source that doesn't exist."""


class DataSourceImproperlyConfigured(Exception):
    """Raised when trying to dispatch a data_source that is not fully configured."""


class DataSourceNotInSamePage(Exception):
    """
    Raised when trying to move a data_source before a data_source on a different
    page.
    """

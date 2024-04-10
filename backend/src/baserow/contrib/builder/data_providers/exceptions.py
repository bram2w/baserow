class DataProviderChunkInvalidException(Exception):
    """
    An exception raised when `get_data_chunk` validates its data
    and finds that it is invalid.
    """


class FormDataProviderChunkInvalidException(DataProviderChunkInvalidException):
    """
    An exception raised when `FormDataProvider` finds that its form data does
    not pass element validation checks.
    """

class InvalidSortDirectionException(Exception):
    """
    Raised when an invalid sort direction is provided.
    """


class InvalidSortAttributeException(Exception):
    """
    Raised when a sort is requested for an invalid or non-existent field.
    """

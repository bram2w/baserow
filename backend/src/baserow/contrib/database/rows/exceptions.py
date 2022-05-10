class RowDoesNotExist(Exception):
    """Raised when trying to get rows that don't exist."""

    def __init__(self, ids, *args, **kwargs):
        if not isinstance(ids, list):
            ids = [ids]
        self.ids = ids
        super().__init__(*args, **kwargs)


class RowIdsNotUnique(Exception):
    """Raised when trying to update the same rows multiple times"""

    def __init__(self, ids, *args, **kwargs):
        self.ids = ids
        super().__init__(*args, **kwargs)

class PageDoesNotExist(Exception):
    """Raised when trying to get a page that doesn't exist."""


class PageNotInBuilder(Exception):
    """Raised when trying to get a page that does not belong to the correct builder"""

    def __init__(self, page_id=None, *args, **kwargs):
        self.page_id = page_id
        super().__init__(
            f"The page {page_id} does not belong to the builder.",
            *args,
            **kwargs,
        )

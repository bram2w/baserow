class ElementDoesNotExist(Exception):
    """Raised when trying to get an element that doesn't exist."""


class ElementNotInPage(Exception):
    """Raised when trying to get an element that does not belong to the correct page"""

    def __init__(self, element_id=None, *args, **kwargs):
        self.element_id = element_id
        super().__init__(
            f"The element {element_id} does not belong to the page.",
            *args,
            **kwargs,
        )

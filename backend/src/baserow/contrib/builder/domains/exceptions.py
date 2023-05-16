class DomainDoesNotExist(Exception):
    """Raised when trying to get a domain that doesn't exist."""


class DomainNotInBuilder(Exception):
    """Raised when trying to get a domain that does not belong to the correct builder"""

    def __init__(self, domain_id=None, *args, **kwargs):
        self.domain_id = domain_id
        super().__init__(
            f"The domain {domain_id} does not belong to the builder.",
            *args,
            **kwargs,
        )

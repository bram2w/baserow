from baserow.core.exceptions import (
    InstanceTypeDoesNotExist, InstanceTypeAlreadyRegistered
)


class ViewDoesNotExist(Exception):
    """Raised when trying to get a view that doesn't exist."""


class ViewTypeAlreadyRegistered(InstanceTypeAlreadyRegistered):
    pass


class ViewTypeDoesNotExist(InstanceTypeDoesNotExist):
    pass

from baserow.core.exceptions import (
    InstanceTypeDoesNotExist, InstanceTypeAlreadyRegistered
)


class ViewDoesNotExist(Exception):
    """Raised when trying to get a view that doesn't exist."""


class UnrelatedFieldError(Exception):
    """
    Raised when a field is not related to the view. For example when someone tries to
    update field options of a field that does not belong to the view's table.
    """


class ViewTypeAlreadyRegistered(InstanceTypeAlreadyRegistered):
    pass


class ViewTypeDoesNotExist(InstanceTypeDoesNotExist):
    pass

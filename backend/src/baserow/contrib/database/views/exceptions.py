from baserow.core.exceptions import (
    InstanceTypeDoesNotExist,
    InstanceTypeAlreadyRegistered,
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


class ViewFilterDoesNotExist(Exception):
    """Raised when trying to get a view filter that does not exist."""


class ViewFilterNotSupported(Exception):
    """Raised when the view type does not support filters."""


class ViewFilterTypeNotAllowedForField(Exception):
    """Raised when the view filter type is compatible with the field type."""

    def __init__(self, filter_type=None, field_type=None, *args, **kwargs):
        self.filter_type = filter_type
        self.field_type = field_type
        super().__init__(
            f"The view filter type {filter_type} is not compatible with field type "
            f"{field_type}.",
            *args,
            **kwargs,
        )


class ViewFilterTypeDoesNotExist(InstanceTypeDoesNotExist):
    """Raised when the view filter type was not found in the registry."""


class ViewFilterTypeAlreadyRegistered(InstanceTypeAlreadyRegistered):
    """Raised when the view filter type is already registered in the registry."""


class ViewSortDoesNotExist(Exception):
    """Raised when trying to get a view sort that does not exist."""


class ViewSortNotSupported(Exception):
    """Raised when the view type does not support sorting."""


class ViewSortFieldAlreadyExist(Exception):
    """Raised when a view sort with the field type already exists."""


class ViewSortFieldNotSupported(Exception):
    """Raised when a field does not supports sorting in a view."""

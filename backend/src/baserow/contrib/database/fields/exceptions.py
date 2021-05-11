from baserow.core.exceptions import (
    InstanceTypeDoesNotExist,
    InstanceTypeAlreadyRegistered,
)


class FieldTypeAlreadyRegistered(InstanceTypeAlreadyRegistered):
    pass


class FieldTypeDoesNotExist(InstanceTypeDoesNotExist):
    pass


class FieldNotInTable(Exception):
    """Raised when the field does not belong to a table."""


class FieldDoesNotExist(Exception):
    """Raised when the requested field does not exist."""


class PrimaryFieldAlreadyExists(Exception):
    """Raised if a primary field is created, but is already exists for the table."""


class CannotDeletePrimaryField(Exception):
    """Raised if the user tries to delete the primary field which is not allowed."""


class CannotChangeFieldType(Exception):
    """Raised if the field type cannot be altered."""


class LinkRowTableNotProvided(Exception):
    """
    Raised when a link row field is trying to be created without the provided link
    row table.
    """


class LinkRowTableNotInSameDatabase(Exception):
    """
    Raised when the desired link row table is not in the same database as the table.
    """


class MaxFieldLimitExceeded(Exception):
    """ Raised when the field count exceeds the limit"""


class OrderByFieldNotFound(Exception):
    """Raised when the field was not found in the table."""

    def __init__(self, field_name=None, *args, **kwargs):
        self.field_name = field_name
        super().__init__(*args, **kwargs)


class OrderByFieldNotPossible(Exception):
    """Raised when it is not possible to order by a field."""

    def __init__(self, field_name=None, field_type=None, *args, **kwargs):
        self.field_name = field_name
        self.field_type = field_type
        super().__init__(*args, **kwargs)


class FilterFieldNotFound(Exception):
    """Raised when the field was not found in the table."""

    def __init__(self, field_name=None, *args, **kwargs):
        self.field_name = field_name
        super().__init__(*args, **kwargs)


class IncompatiblePrimaryFieldTypeError(Exception):
    """Raised when the primary field is changed to an incompatible field type."""

    def __init__(self, field_type=None, *args, **kwargs):
        self.field_type = field_type
        super().__init__(*args, **kwargs)

from baserow.core.exceptions import (
    InstanceTypeDoesNotExist, InstanceTypeAlreadyRegistered
)


class FieldTypeAlreadyRegistered(InstanceTypeAlreadyRegistered):
    pass


class FieldTypeDoesNotExist(InstanceTypeDoesNotExist):
    pass


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

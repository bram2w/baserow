class CannotRestoreChildBeforeParent(Exception):
    """
    Raised when attempting to restore a trashed item when it's parent is also trashed.
    """


class ParentIdMustBeProvidedException(Exception):
    """
    Raised when attempting to access or restore a trashed item without providing it's
    parent's id.
    """


class ParentIdMustNotBeProvidedException(Exception):
    """
    Raised when attempting to access or restore a trashed item which should not have
    it's parent id provided, but it was anyway.
    """


class CannotDeleteAlreadyDeletedItem(Exception):
    """
    Raised when attempting to delete an item which has already been deleted.
    """

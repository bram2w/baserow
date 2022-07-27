class SnapshotDoesNotExist(Exception):
    """Raise when trying to get a snapshot that does not exist."""


class MaximumSnapshotsReached(Exception):
    """Raise when a new snapshot cannot be created since the max limit is reached."""


class SnapshotIsBeingCreated(Exception):
    """
    Raise when a manipulation with a snapshot is prohibited
    since it is being created.
    """


class SnapshotIsBeingRestored(Exception):
    """
    Raise when a manipulation with a snapshot is prohibited
    since it is being restored.
    """


class SnapshotIsBeingDeleted(Exception):
    """
    Raise when a manipulation with a snapshot is prohibited
    since it is being deleted.
    """


class SnapshotNameNotUnique(Exception):
    """
    Raise when a snapshot name is not unique per application.
    """

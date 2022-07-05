from baserow.core.exceptions import (
    InstanceTypeDoesNotExist,
    InstanceTypeAlreadyRegistered,
)


class JobDoesNotExist(Exception):
    """Raised when the job does not exist."""


class MaxJobCountExceeded(Exception):
    """
    Raised when a user starts another job while max count jobs are already running.
    """


class JobTypeDoesNotExist(InstanceTypeDoesNotExist):
    """Raised when trying to get a job type that does not exist."""


class JobTypeAlreadyRegistered(InstanceTypeAlreadyRegistered):
    """
    Raised when trying to register a job type that exists
    already.
    """

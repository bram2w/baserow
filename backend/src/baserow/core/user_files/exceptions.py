import math


class InvalidFileStreamError(Exception):
    """Raised when the provided file stream is invalid."""


class FileSizeTooLargeError(Exception):
    """Raised when the provided file is too large."""

    def __init__(self, max_size_bytes, *args, **kwargs):
        self.max_size_mb = math.floor(max_size_bytes / 1024 / 1024)
        super().__init__(*args, **kwargs)


class FileURLCouldNotBeReached(Exception):
    """
    Raised when the provided URL could not be reached or points to an internal
    service.
    """


class InvalidFileURLError(Exception):
    """Raised when the provided file URL is invalid."""


class InvalidUserFileNameError(Exception):
    """Raised when the provided user file name is invalid."""

    def __init__(self, name, *args, **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)


class UserFileDoesNotExist(Exception):
    """Raised when a user file with the provided name or id does not exist."""

    def __init__(self, name_or_id, *args, **kwargs):
        self.name_or_id = name_or_id
        super().__init__(*args, **kwargs)


class MaximumUniqueTriesError(Exception):
    """
    Raised when the maximum tries has been exceeded while generating a unique user file
    string.
    """

from django.core.files.storage import Storage, default_storage


def get_default_storage() -> Storage:
    """
    Returns the default storage. This method is mainly used to have
    a single point of entry for the default storage, so it's easier to
    test and mock.

    :return: The django default storage.
    """

    return default_storage


class OverwritingStorageHandler:
    def __init__(self, storage=None):
        self.storage = storage or get_default_storage()

    def save(self, name, content):
        if self.storage.exists(name):
            self.storage.delete(name)
        self.storage.save(name, content)

from django.core.files.storage import default_storage


class OverwritingStorageHandler:
    def __init__(self, storage):
        self.storage = storage if storage else default_storage

    def save(self, name, content):
        if self.storage.exists(name):
            self.storage.delete(name)
        self.storage.save(name, content)

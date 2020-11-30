from django.core.files.storage import FileSystemStorage


class OverwriteFileSystemStorage(FileSystemStorage):
    def _save(self, name, content):
        if self.exists(name):
            self.delete(name)
        return super()._save(name, content)

    def get_available_name(self, name, *args, **kwargs):
        return name

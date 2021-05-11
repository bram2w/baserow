from PIL import Image

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage

from baserow.core.user_files.models import UserFile
from baserow.core.user_files.handler import UserFileHandler


class Command(BaseCommand):
    help = (
        "Regenerates all the user file thumbnails based on the current settings. "
        "Existing files will be overwritten."
    )

    def handle(self, *args, **options):
        """
        Regenerates the thumbnails of all image user files. If the USER_THUMBNAILS
        setting ever changes then this file can be used to fix all the thumbnails.
        """

        i = 0
        handler = UserFileHandler()
        buffer_size = 100
        queryset = UserFile.objects.filter(is_image=True)
        count = queryset.count()

        while i < count:
            user_files = queryset[i : min(count, i + buffer_size)]
            for user_file in user_files:
                i += 1

                full_path = handler.user_file_path(user_file)
                stream = default_storage.open(full_path)

                try:
                    image = Image.open(stream)
                    handler.generate_and_save_image_thumbnails(
                        image, user_file, storage=default_storage
                    )
                    image.close()
                except IOError:
                    pass

                stream.close()

        self.stdout.write(self.style.SUCCESS(f"{i} thumbnails have been regenerated."))

import pathlib
import mimetypes

from os.path import join
from io import BytesIO
from urllib.parse import urlparse

import advocate
from advocate.exceptions import UnacceptableAddressException
from requests.exceptions import RequestException

from PIL import Image, ImageOps

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

from baserow.core.utils import sha256_hash, stream_size, random_string, truncate_middle

from .exceptions import (
    InvalidFileStreamError,
    FileSizeTooLargeError,
    FileURLCouldNotBeReached,
    MaximumUniqueTriesError,
    InvalidFileURLError,
)
from .models import UserFile


class UserFileHandler:
    def user_file_path(self, user_file_name):
        """
        Generates the full user file path based on the provided file name. This path
        can be used with the storage.

        :param user_file_name: The user file name.
        :type user_file_name: str
        :return: The generated path.
        :rtype: str
        """

        if isinstance(user_file_name, UserFile):
            user_file_name = user_file_name.name

        return join(settings.USER_FILES_DIRECTORY, user_file_name)

    def user_file_thumbnail_path(self, user_file_name, thumbnail_name):
        """
        Generates the full user file thumbnail path based on the provided filename.
        This path can be used with the storage.

        :param user_file_name: The user file name.
        :type user_file_name: str
        :param thumbnail_name: The thumbnail type name.
        :type thumbnail_name: str
        :return: The generated path.
        :rtype: str
        """

        if isinstance(user_file_name, UserFile):
            user_file_name = user_file_name.name

        return join(settings.USER_THUMBNAILS_DIRECTORY, thumbnail_name, user_file_name)

    def generate_unique(self, sha256_hash, extension, length=32, max_tries=1000):
        """
        Generates a unique non existing string for a new user file.

        :param sha256_hash: The hash of the file name. Needed because they are
            required to be unique together.
        :type sha256_hash: str
        :param extension: The extension of the file name. Needed because they are
            required to be unique together.
        :type extension: str
        :param length: Indicates the amount of characters that the unique must contain.
        :type length: int
        :param max_tries: The maximum amount of tries to check if a unique already
            exists.
        :type max_tries: int
        :raises MaximumUniqueTriesError: When the maximum amount of tries has
            been exceeded.
        :return: The generated unique string
        :rtype: str
        """

        i = 0

        while True:
            if i > max_tries:
                raise MaximumUniqueTriesError(
                    f"Tried {max_tries} tokens, but none of them are unique."
                )

            i += 1
            unique = random_string(length)

            if not UserFile.objects.filter(
                sha256_hash=sha256_hash, original_extension=extension, unique=unique
            ).exists():
                return unique

    def generate_and_save_image_thumbnails(self, image, user_file, storage=None):
        """
        Generates the thumbnails based on the current settings and saves them to the
        provided storage. Note that existing files with the same name will be
        overwritten.

        :param image: The original Pillow image that serves as base when generating the
            the image.
        :type image: Image
        :param user_file: The user file for which the thumbnails must be generated
            and saved.
        :type user_file: UserFile
        :param storage: The storage where the thumbnails must be saved to.
        :type storage: Storage or None
        :raises ValueError: If the provided user file is not a valid image.
        """

        if not user_file.is_image:
            raise ValueError("The provided user file is not an image.")

        storage = storage or default_storage
        image_width = user_file.image_width
        image_height = user_file.image_height

        for name, size in settings.USER_THUMBNAILS.items():
            size_copy = size.copy()

            # If the width or height is None we want to keep the aspect ratio.
            if size_copy[0] is None and size_copy[1] is not None:
                size_copy[0] = round(image_width / image_height * size_copy[1])
            elif size_copy[1] is None and size_copy[0] is not None:
                size_copy[1] = round(image_height / image_width * size_copy[0])

            thumbnail = ImageOps.fit(image.copy(), size_copy, Image.ANTIALIAS)
            thumbnail_stream = BytesIO()
            thumbnail.save(thumbnail_stream, image.format)
            thumbnail_stream.seek(0)
            thumbnail_path = self.user_file_thumbnail_path(user_file, name)
            storage.save(thumbnail_path, thumbnail_stream)

            del thumbnail
            del thumbnail_stream

    def upload_user_file(self, user, file_name, stream, storage=None):
        """
        Saves the provided uploaded file in the provided storage. If no storage is
        provided the default_storage will be used. An entry into the user file table
        is also created.

        :param user: The user on whose behalf the file is uploaded.
        :type user: User
        :param file_name: The provided file name when the file was uploaded.
        :type file_name: str
        :param stream: An IO stream containing the uploaded file.
        :type stream: IOBase
        :param storage: The storage where the file must be saved to.
        :type storage: Storage
        :raises InvalidFileStreamError: If the provided stream is invalid.
        :raises FileSizeToLargeError: If the provided content is too large.
        :return: The newly created user file.
        :rtype: UserFile
        """

        if not hasattr(stream, "read"):
            raise InvalidFileStreamError("The provided stream is not readable.")

        size = stream_size(stream)

        if size > settings.USER_FILE_SIZE_LIMIT:
            raise FileSizeTooLargeError(
                settings.USER_FILE_SIZE_LIMIT, "The provided file is too large."
            )

        storage = storage or default_storage
        hash = sha256_hash(stream)
        file_name = truncate_middle(file_name, 64)

        try:
            return UserFile.objects.get(original_name=file_name, sha256_hash=hash)
        except UserFile.DoesNotExist:
            pass

        extension = pathlib.Path(file_name).suffix[1:].lower()
        mime_type = mimetypes.guess_type(file_name)[0] or ""
        unique = self.generate_unique(hash, extension)

        # By default the provided file is not an image.
        image = None
        is_image = False
        image_width = None
        image_height = None

        # Try to open the image with Pillow. If that succeeds we know the file is an
        # image.
        try:
            image = Image.open(stream)
            is_image = True
            image_width = image.width
            image_height = image.height
        except IOError:
            pass

        user_file = UserFile.objects.create(
            original_name=file_name,
            original_extension=extension,
            size=size,
            mime_type=mime_type,
            unique=unique,
            uploaded_by=user,
            sha256_hash=hash,
            is_image=is_image,
            image_width=image_width,
            image_height=image_height,
        )

        # If the uploaded file is an image we need to generate the configurable
        # thumbnails for it. We want to generate them before the file is saved to the
        # storage because some storages close the stream after saving.
        if image:
            self.generate_and_save_image_thumbnails(image, user_file, storage=storage)

            # When all the thumbnails have been generated, the image can be deleted
            # from memory.
            del image

        # Save the file to the storage.
        full_path = self.user_file_path(user_file)
        storage.save(full_path, stream)

        # Close the stream because we don't need it anymore.
        stream.close()

        return user_file

    def upload_user_file_by_url(self, user, url, storage=None):
        """
        Uploads a user file by downloading it from the provided URL.

        :param user: The user on whose behalf the file is uploaded.
        :type user: User
        :param url: The URL where the file must be downloaded from.
        :type url: str
        :param storage: The storage where the file must be saved to.
        :type storage: Storage
        :raises FileURLCouldNotBeReached: If the file could not be downloaded from
            the URL or if it points to an internal service.
        :raises InvalidFileURLError: If the provided file url is invalid.
        :return: The newly created user file.
        :rtype: UserFile
        """

        parsed_url = urlparse(url)

        if parsed_url.scheme not in ["http", "https"]:
            raise InvalidFileURLError("Only http and https are allowed.")

        file_name = url.split("/")[-1]

        try:
            response = advocate.get(url, stream=True, timeout=10)

            if not response.ok:
                raise FileURLCouldNotBeReached(
                    "The response did not respond with an " "OK status code."
                )

            content = response.raw.read(
                settings.USER_FILE_SIZE_LIMIT + 1, decode_content=True
            )
        except (RequestException, UnacceptableAddressException):
            raise FileURLCouldNotBeReached("The provided URL could not be reached.")

        file = SimpleUploadedFile(file_name, content)
        return UserFileHandler().upload_user_file(user, file_name, file, storage)

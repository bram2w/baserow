from rest_framework.exceptions import ValidationError

from baserow.core.user_files.models import UserFile


def image_file_validation(file: UserFile) -> None:
    """
    Validate that the file that is being set as the image source, is in fact an image

    :param file: The image file
    :raises ValidationError: If the file does not exist or is not an image
    """

    if not file.is_image:
        raise ValidationError(f"The file with name {file.name} is not an image")

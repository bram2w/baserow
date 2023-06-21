from rest_framework.exceptions import ValidationError

from baserow.core.user_files.models import UserFile


def image_file_id_validation(value: int) -> None:
    """
    Validate that the file that is being set as the image source, is in fact an image

    :param value: The id of the image file
    :raises ValidationError: If the file does not exist or is not an image
    """

    try:
        file = UserFile.objects.get(id=value)
    except UserFile.DoesNotExist:
        raise ValidationError(f"The file with id {value} does not exist")

    if not file.is_image:
        raise ValidationError(f"The file with id {value} is not an image")

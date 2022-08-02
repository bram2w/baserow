from rest_framework.exceptions import ValidationError

from baserow.core.user_files.exceptions import InvalidUserFileNameError
from baserow.core.user_files.models import UserFile


def user_file_name_validator(value):
    try:
        UserFile.deconstruct_name(value)
    except InvalidUserFileNameError:
        raise ValidationError("The user file name is invalid.", code="invalid")

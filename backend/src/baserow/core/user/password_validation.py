from django.core.exceptions import ValidationError


class MaximumLengthValidator:
    """
    Validate whether the password is of a maximum length.
    """

    def __init__(self, max_length=256):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            error = (
                f"This password is too long. "
                f"It must not exceed {self.max_length} character"
                f"{'s' if self.max_length != 1 else ''}."
            )
            raise ValidationError(
                error,
                code="password_too_long",
                params={"max_length": self.max_length},
            )

    def get_help_text(self):
        return (
            f"Your password must not exceed {self.max_length} character"
            f"{'s' if self.max_length != 1 else ''}."
        )

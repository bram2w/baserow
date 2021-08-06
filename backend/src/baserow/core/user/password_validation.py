from django.core.exceptions import ValidationError
from django.utils.translation import ngettext


class MaximumLengthValidator:
    """
    Validate whether the password is of a maximum length.
    """

    def __init__(self, max_length=256):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            error_singular = (
                "This password is too long. "
                "It must not exceed %(max_length)d character."
            )

            error_plural = (
                "This password is too long. "
                "It must not exceed %(max_length)d characters."
            )
            raise ValidationError(
                ngettext(error_singular, error_plural, self.max_length),
                code="password_too_long",
                params={"max_length": self.max_length},
            )

    def get_help_text(self):
        return (
            ngettext(
                "Your password must not exceed %(max_length)d character.",
                "Your password must not exceed %(max_length)d characters.",
                self.max_length,
            )
            % {"max_length": self.max_length}
        )

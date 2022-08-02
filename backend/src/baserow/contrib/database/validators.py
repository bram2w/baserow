from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.functional import SimpleLazyObject

import regex


def _lazy_re_compile(regex_value, flags=0):
    """Lazily compile a regex with flags."""

    def _compile():
        # Compile the regex if it was not passed pre-compiled.
        if isinstance(regex_value, str):
            return regex.compile(regex_value, flags)
        else:
            # Dev only warning, fine if this is not run in real code, this is a copied
            # module see the docstring on UnicodeRegexValidator
            assert (  # nosec
                not flags
            ), "flags must be empty if regex is passed pre-compiled"
            return regex_value

    return SimpleLazyObject(_compile)


@deconstructible
class UnicodeRegexValidator:
    """
    Amazingly the standard python re regex library does not correctly match valid
    unicode word characters https://bugs.python.org/issue12731 ...

    This is an exact copy of Django's Regex validator, but instead using the swap in
    replacement regex library instead of re, which does handle unicode correctly!
    """

    regex = ""
    message = "Enter a valid value."
    code = "invalid"
    inverse_match = False
    flags = 0

    def __init__(
        self, regex_value=None, message=None, code=None, inverse_match=None, flags=None
    ):
        if regex_value is not None:
            self.regex_value = regex_value
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if inverse_match is not None:
            self.inverse_match = inverse_match
        if flags is not None:
            self.flags = flags
        if self.flags and not isinstance(self.regex_value, str):
            raise TypeError(
                "If the flags are set, regex must be a regular expression string."
            )

        self.regex_value = _lazy_re_compile(self.regex_value, self.flags)

    def __call__(self, value):
        """
        Validate that the input contains (or does *not* contain, if
        inverse_match is True) a match for the regular expression.
        """

        regex_matches = self.regex_value.search(str(value))
        invalid_input = regex_matches if self.inverse_match else not regex_matches
        if invalid_input:
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        return (
            isinstance(other, UnicodeRegexValidator)
            and self.regex_value.pattern == other.regex_value.pattern
            and self.regex_value.flags == other.regex_value.flags
            and (self.message == other.message)
            and (self.code == other.code)
            and (self.inverse_match == other.inverse_match)
        )

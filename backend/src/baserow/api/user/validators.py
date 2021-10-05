from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.conf import settings


def password_validation(value):
    """
    Verifies that the provided password adheres to the password validation as defined
    in the django core settings.
    """

    try:
        validate_password(value)
    except ValidationError as e:
        raise serializers.ValidationError(
            e.messages[0], code="password_validation_failed"
        )

    return value


def language_validation(value):
    """
    Verifies that the provided language is known.
    """

    valid_languages = [lang[0] for lang in settings.LANGUAGES]
    if value not in valid_languages:
        raise serializers.ValidationError(
            f"Only the following language keys are valid: {','.join(valid_languages)}",
            code="invalid_language",
        )

    return value

import validators
from rest_framework import serializers


def validate_domain(value):
    if value and not validators.domain(value):
        raise serializers.ValidationError(
            "The domain value is not a valid domain name."
        )

    return value

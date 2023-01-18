import json

from django.utils.dateparse import parse_datetime

from rest_framework import serializers


def validate_datetime_str(value):
    try:
        if parse_datetime(value) is None:
            raise ValueError
    except ValueError:
        raise serializers.ValidationError(f"Invalid timestamp value '{value}'.")


def audit_log_list_filters_validator(value):
    """
    Validates the filters query parameter. It should be a valid JSON object.
    It also check the timestamp to be valid so to avoid the backend
    to crash when it tries to parse it.
    """

    try:
        filters = json.loads(value)
    except json.JSONDecodeError:
        raise serializers.ValidationError("Invalid filters JSON.")
    for key in ["to_timestamp", "from_timestamp"]:
        if timestamp := filters.get(key):
            validate_datetime_str(timestamp)

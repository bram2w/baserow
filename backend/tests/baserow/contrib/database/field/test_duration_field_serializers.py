from datetime import timedelta

import pytest
from rest_framework import serializers

from baserow.contrib.database.api.fields.serializers import DurationFieldSerializer
from baserow.contrib.database.fields.utils.duration import (
    DURATION_FORMAT_TOKENS,
    DURATION_FORMATS,
)


@pytest.mark.parametrize(
    "duration_format,user_input,saved_value",
    [
        # Normal input:
        ("h:mm", 0, timedelta(seconds=0)),
        ("h:mm", 3660, timedelta(seconds=3660)),
        ("h:mm", 86400, timedelta(days=1)),
        ("h:mm:ss", 0, timedelta(seconds=0)),
        ("h:mm:ss", 3661, timedelta(seconds=3661)),
        ("h:mm:ss.s", 3661.1, timedelta(seconds=3661.1)),
        ("h:mm:ss.ss", 3661.12, timedelta(seconds=3661.12)),
        ("h:mm:ss.sss", 0, timedelta(seconds=0)),
        ("h:mm:ss.sss", 3661.123, timedelta(seconds=3661.123)),
        # Rounding:
        ("h:mm", 3661.123, timedelta(seconds=3660)),
        ("h:mm", 3661.999, timedelta(seconds=3660)),
        ("h:mm:ss", 3661.123, timedelta(seconds=3661)),
        ("h:mm:ss", 3661.789, timedelta(seconds=3662)),
        ("h:mm:ss.s", 3661.123, timedelta(seconds=3661.1)),
        ("h:mm:ss.s", 3661.789, timedelta(seconds=3661.8)),
        ("h:mm:ss.ss", 3661.123, timedelta(seconds=3661.12)),
        ("h:mm:ss.ss", 3661.789, timedelta(seconds=3661.79)),
        ("h:mm:ss.sss", 3661.1234, timedelta(seconds=3661.123)),
        ("h:mm:ss.sss", 3661.6789, timedelta(seconds=3661.679)),
        # String input:
        ("h:mm", "1:01", timedelta(seconds=3660)),
        ("h:mm:ss", "1:01:01", timedelta(seconds=3661)),
        ("h:mm:ss.s", "1:01:01.1", timedelta(seconds=3661.1)),
        ("h:mm:ss.ss", "1:01:01.12", timedelta(seconds=3661.12)),
        ("h:mm:ss.sss", "1:01:01.123", timedelta(seconds=3661.123)),
        # String input with rounding:
        ("h:mm", "1:01:01.123", timedelta(seconds=3660)),
        ("h:mm", "1:01:01.999", timedelta(seconds=3660)),
        ("h:mm:ss", "1:01:01.123", timedelta(seconds=3661)),
        ("h:mm:ss", "1:01:01.789", timedelta(seconds=3662)),
        ("h:mm:ss.s", "1:01:01.123", timedelta(seconds=3661.1)),
        ("h:mm:ss.s", "1:01:01.789", timedelta(seconds=3661.8)),
        ("h:mm:ss.ss", "1:01:01.123", timedelta(seconds=3661.12)),
        ("h:mm:ss.ss", "1:01:01.789", timedelta(seconds=3661.79)),
        ("h:mm:ss.sss", "1:01:01.1234", timedelta(seconds=3661.123)),
        ("h:mm:ss.sss", "1:01:01.6789", timedelta(seconds=3661.679)),
        # None should be None in every format:
        ("h:mm", None, None),
        ("h:mm:ss", None, None),
        ("h:mm:ss.s", None, None),
        ("h:mm:ss.ss", None, None),
        ("h:mm:ss.sss", None, None),
    ],
)
@pytest.mark.django_db
@pytest.mark.field_duration
def test_duration_serializer_to_internal_value(
    data_fixture, duration_format, user_input, saved_value
):
    """
    Tests that for the Duration Serializer, the value is always serialized as
    seconds for the database for every duration format.
    """

    serializer = DurationFieldSerializer(duration_format=duration_format)
    deserialized_value = serializer.to_internal_value(user_input)
    assert deserialized_value == saved_value, (
        f"{deserialized_value.total_seconds()} != {saved_value.total_seconds()}. "
        f"Input: {user_input} with format: {duration_format}."
    )


@pytest.mark.parametrize(
    "duration_format,user_input",
    [
        ("h:mm", -1),
        ("h:mm", ""),
        ("h:mm", "1.0:1.0"),
        ("h:mm", "1:1:1:1"),
        ("h:mm:ss", "1:1:1:1.1"),
        ("h:mm:ss.s", "aaaaaaa"),
        ("invalid format", 1),
        ("h:m", timedelta.max.total_seconds() + 1),  # Overflow
    ],
)
@pytest.mark.django_db
@pytest.mark.field_duration
def test_duration_serializer_to_internal_value_with_invalid_values(
    data_fixture, duration_format, user_input
):
    serializer = DurationFieldSerializer(duration_format=duration_format)
    with pytest.raises(serializers.ValidationError):
        serializer.to_internal_value(user_input)


@pytest.mark.parametrize(
    "duration_format,user_input,returned_value",
    [
        ("h:mm", 3660, 3660),
        ("h:mm:ss", 3661, 3661),
        ("h:mm:ss.s", 3661.1, 3661.1),
        ("h:mm:ss.ss", 3661.12, 3661.12),
        ("h:mm:ss.sss", 3661.123, 3661.123),
        ("h:mm:ss.sss", 3661.1234, 3661.1234),
    ],
)
@pytest.mark.django_db
@pytest.mark.field_duration
def test_duration_serializer_to_representation(
    data_fixture, duration_format, user_input, returned_value
):
    """
    Tests that for the Duration Serializer, the representation is returned in
    seconds (value.total_seconds()) from the database for every duration format.
    """

    serializer = DurationFieldSerializer(duration_format=duration_format)

    assert serializer.to_representation(timedelta(seconds=user_input)) == returned_value


@pytest.mark.django_db
@pytest.mark.field_duration
def test_duration_token_options(data_fixture):
    """
    Tests that the token options are correct for the duration field.
    """

    for format in DURATION_FORMATS.keys():
        for token in format.split(":"):
            assert token in DURATION_FORMAT_TOKENS, (
                f"{token} not in DURATION_FORMAT_TOKENS. Please add it with the correct "
                "options to be able to convert a formatted string to a timedelta."
            )

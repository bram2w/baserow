from datetime import timedelta

import pytest
from rest_framework import serializers

from baserow.contrib.database.api.fields.serializers import DurationFieldSerializer
from baserow.contrib.database.fields.utils.duration import (
    DURATION_FORMAT_TOKENS,
    DURATION_FORMATS,
    postgres_interval_to_seconds,
    tokenize_formatted_duration,
)


@pytest.mark.parametrize(
    "duration_format,user_input,saved_value",
    [
        # number input:
        ("h:mm", 0, timedelta(seconds=0)),
        ("h:mm", 3660, timedelta(seconds=3660)),
        ("h:mm", 86400, timedelta(days=1)),
        ("h:mm:ss", 0, timedelta(seconds=0)),
        ("h:mm:ss", 3661, timedelta(seconds=3661)),
        ("h:mm:ss.s", 3661.1, timedelta(seconds=3661.1)),
        ("h:mm:ss.ss", 3661.12, timedelta(seconds=3661.12)),
        ("h:mm:ss.sss", 0, timedelta(seconds=0)),
        ("h:mm:ss.sss", 3661.123, timedelta(seconds=3661.123)),
        ("d h", 0, timedelta(seconds=0)),
        ("d h", 3600, timedelta(hours=1)),
        ("d h", 90000, timedelta(days=1, hours=1)),
        ("d h:mm", 0, timedelta(seconds=0)),
        ("d h:mm", 3660, timedelta(hours=1, minutes=1)),
        ("d h:mm", 86400, timedelta(days=1)),
        ("d h:mm:ss", 0, timedelta(seconds=0)),
        ("d h:mm:ss", 3661, timedelta(seconds=3661)),
        ("d h mm", 3661, timedelta(seconds=3660)),
        ("d h mm ss", 3661, timedelta(seconds=3661)),
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
        ("d h", 86400 + 3600.123, timedelta(days=1, hours=1)),
        ("d h", 29.9 * 60, timedelta(seconds=0)),
        ("d h", 30 * 60, timedelta(hours=1)),
        ("d h:mm", 29, timedelta(seconds=0)),
        ("d h:mm", 30, timedelta(minutes=1)),
        ("d h:mm:ss", 0.49, timedelta(seconds=0)),
        ("d h:mm:ss", 0.5, timedelta(seconds=1)),
        # String input:
        ("h:mm", "1:01", timedelta(seconds=3660)),
        ("h:mm:ss", "1:01:01", timedelta(seconds=3661)),
        ("h:mm:ss.s", "1:01:01.1", timedelta(seconds=3661.1)),
        ("h:mm:ss.ss", "1:01:01.12", timedelta(seconds=3661.12)),
        ("h:mm:ss.sss", "1:01:01.123", timedelta(seconds=3661.123)),
        ("d h", "1 1", timedelta(days=1, hours=1)),
        ("d h", "1d1h", timedelta(days=1, hours=1)),
        ("d h", "1d 1h", timedelta(days=1, hours=1)),
        ("d h", "1 1h", timedelta(days=1, hours=1)),
        ("d h", "1d 1", timedelta(days=1, hours=1)),
        ("d h", "1d1", timedelta(days=1, hours=1)),
        ("d h", "12h", timedelta(hours=12)),
        ("d h", "3d", timedelta(days=3)),
        ("d h:mm", "1 1:01", timedelta(days=1, seconds=3660)),
        ("d h:mm", "1d1:01", timedelta(days=1, seconds=3660)),
        ("d h:mm", "1d 1:01", timedelta(days=1, seconds=3660)),
        ("d h:mm", "1 1:1", timedelta(days=1, seconds=3660)),
        ("d h:mm", "1d1:1", timedelta(days=1, seconds=3660)),
        ("d h:mm", "1d 1:1", timedelta(days=1, seconds=3660)),
        ("d h:mm:ss", "1 1:01:01", timedelta(days=1, seconds=3661)),
        ("d h:mm:ss", "1d1:01:01", timedelta(days=1, seconds=3661)),
        ("d h:mm:ss", "1d 1:01:01", timedelta(days=1, seconds=3661)),
        ("d h:mm:ss", "1 1:1:1", timedelta(days=1, seconds=3661)),
        ("d h:mm:ss", "1d1:1:1", timedelta(days=1, seconds=3661)),
        ("d h:mm:ss", "1d 1:1:1", timedelta(days=1, seconds=3661)),
        ("d h mm", "1d 123", timedelta(days=1, minutes=123)),
        ("d h mm", "123", timedelta(seconds=120)),
        ("d h mm ss", "1d 123", timedelta(days=1, seconds=123)),
        ("d h mm ss", "123", timedelta(seconds=123)),
        ("d h mm ss", "2h 3s", timedelta(hours=2, seconds=3)),
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
        ("d h", "1 1:01:01.123", timedelta(days=1, hours=1)),
        ("d h", "1.123", timedelta(seconds=0)),
        ("d h", "29:59.999", timedelta(seconds=0)),
        ("d h", "30:00", timedelta(hours=30)),
        ("d h", "30:00.001", timedelta(hours=1)),
        ("d h:mm", "1 1:01:01.123", timedelta(days=1, hours=1, minutes=1)),
        ("d h:mm", "1.123", timedelta(seconds=0)),
        ("d h:mm", "29.999", timedelta(seconds=0)),
        ("d h:mm", "30", timedelta(minutes=1)),
        ("d h:mm", "30.001", timedelta(minutes=1)),
        ("d h:mm:ss", "1 1:01:01.123", timedelta(days=1, seconds=3661)),
        ("d h:mm:ss", "1.123", timedelta(seconds=1)),
        ("d h:mm:ss", "29.999", timedelta(seconds=30)),
        ("d h:mm:ss", "70", timedelta(seconds=70)),
        ("d h:mm:ss", "0.5", timedelta(seconds=1)),
        # None should be None in every format:
        ("h:mm", None, None),
        ("h:mm:ss", None, None),
        ("h:mm:ss.s", None, None),
        ("h:mm:ss.ss", None, None),
        ("h:mm:ss.sss", None, None),
        ("d h", None, None),
        ("d h:mm", None, None),
        ("d h:mm:ss", None, None),
        ("d h mm", None, None),
        ("d h mm ss", None, None),
    ],
)
@pytest.mark.field_duration
def test_duration_serializer_to_internal_value(
    duration_format, user_input, saved_value
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
    "user_input,parsed_value",
    (
        ("1 year", timedelta(days=365)),
        ("2 mons", timedelta(days=60)),
        ("3 days", timedelta(days=3)),
        ("04:05:06", timedelta(hours=4, minutes=5, seconds=6)),
        (
            "1 year 2 mons 3 days 04:05:06",
            timedelta(days=365 + 60 + 3, hours=4, minutes=5, seconds=6),
        ),
        (
            "-1 year -2 mons +3 days 04:05:06",
            timedelta(days=-(365 + 60) + 3, hours=4, minutes=5, seconds=6),
        ),
        (
            "1 year 2 mons -3 days 04:05:06",
            timedelta(days=365 + 60 - 3, hours=4, minutes=5, seconds=6),
        ),
        ("1 year 1 mon 1 day", timedelta(days=365 + 30 + 1)),
        ("2 years 2 mons", timedelta(days=365 * 2 + 60)),
        ("1 year 1:02:03", timedelta(days=365, hours=1, minutes=2, seconds=3)),
        ("2 mons 3 days", timedelta(days=60 + 3)),
        ("3 days 03:04:05", timedelta(days=3, hours=3, minutes=4, seconds=5)),
        ("04:05:06", timedelta(hours=4, minutes=5, seconds=6)),
    ),
)
def test_postgres_interval_to_seconds(user_input, parsed_value):
    assert postgres_interval_to_seconds(user_input) == parsed_value.total_seconds()


@pytest.mark.parametrize(
    "duration_format,user_input",
    [
        ("h:mm", ""),
        ("h:mm", "1.0:1.0"),
        ("h:mm", "1:1:1:1"),
        ("h:mm:ss", "1:1:1:1.1"),
        ("h:mm:ss.s", "aaaaaaa"),
        ("invalid format", 1),
        ("h:m", timedelta.max.total_seconds() + 1),  # Overflow
        ("d h", "1dd"),
        ("d h", "1hh"),
        ("d h", "1d1d"),
        ("d h", "1h1h"),
        ("d h mm", "1h1h"),
        ("d h mm", "1h1h"),
    ],
)
@pytest.mark.field_duration
def test_duration_serializer_to_internal_value_with_invalid_values(
    duration_format, user_input
):
    serializer = DurationFieldSerializer(duration_format=duration_format)
    with pytest.raises(serializers.ValidationError):
        serializer.to_internal_value(user_input)


@pytest.mark.parametrize(
    "duration_format,formula_lookup_value,serialized_value",
    [
        ("h:mm", timedelta(seconds=0), 0),
        ("h:mm", timedelta(hours=1, minutes=1), 3660),
        ("h:mm:ss", timedelta(hours=1, minutes=1, seconds=1), 3661),
        ("h:mm:ss.s", timedelta(hours=1, minutes=1, seconds=1.1), 3661.1),
        ("h:mm:ss.ss", timedelta(hours=1, minutes=1, seconds=1.12), 3661.12),
        ("h:mm:ss.sss", timedelta(hours=1, minutes=1, seconds=1.123), 3661.123),
        ("h:mm:ss.sss", timedelta(hours=1, minutes=1, seconds=1.1234), 3661.1234),
        ("d h", timedelta(days=1, hours=1), 90000),
        ("d h:mm", timedelta(days=1, hours=1, minutes=1), 90060),
        ("d h:mm:ss", timedelta(days=1, hours=1, minutes=1, seconds=1), 90061),
        # the field format doesn't matter for the following tests. Lookups return
        # durations as strings in the postgres interval format, and those value don't
        # depend on the field format.
        (
            "d h:mm:ss",
            "1 year 1 mon 1 day",
            timedelta(days=365 + 30 + 1).total_seconds(),
        ),
        (
            "d h:mm:ss",
            "2 years 2 mons",
            timedelta(days=365 * 2 + 60).total_seconds(),
        ),
        (
            "d h:mm:ss",
            "1 year 1:02:03",
            timedelta(days=365, hours=1, minutes=2, seconds=3).total_seconds(),
        ),
        (
            "d h:mm:ss",
            "2 mons 3 days",
            timedelta(days=60 + 3).total_seconds(),
        ),
        (
            "d h:mm:ss",
            "3 days 03:04:05",
            timedelta(days=3, hours=3, minutes=4, seconds=5).total_seconds(),
        ),
    ],
)
@pytest.mark.field_duration
def test_duration_serializer_to_representation(
    duration_format, formula_lookup_value, serialized_value
):
    serializer = DurationFieldSerializer(duration_format=duration_format)
    assert serializer.to_representation(formula_lookup_value) == serialized_value


@pytest.mark.field_duration
def test_duration_token_options():
    """
    Tests that format are made of tokens that are in DURATION_FORMAT_TOKENS.
    """

    for format in DURATION_FORMATS.keys():
        for token in tokenize_formatted_duration(format):
            assert token in DURATION_FORMAT_TOKENS, (
                f"{token} not in DURATION_FORMAT_TOKENS. Please add it with the correct "
                "options to be able to convert a formatted string to a timedelta."
            )

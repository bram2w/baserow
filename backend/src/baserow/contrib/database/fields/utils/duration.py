from datetime import timedelta
from typing import Optional, Union

from django.core.exceptions import ValidationError

DURATION_FORMATS = {
    "h:mm": {
        "name": "hours:minutes",
        "backup_field_if_changing_to": set(),
        "round_func": lambda value: round(value / 60, 0) * 60,
        "sql_round_func": "(EXTRACT(EPOCH FROM p_in::INTERVAL) / 60)::int * 60",
        "format_func": lambda hours, mins, _: "%d:%02d" % (hours, mins),
    },
    "h:mm:ss": {
        "name": "hours:minutes:seconds",
        "backup_field_if_changing_to": {"h:mm"},
        "round_func": lambda value: round(value, 0),
        "sql_round_func": "EXTRACT(EPOCH FROM p_in::INTERVAL)::int",
        "format_func": lambda hours, mins, secs: "%d:%02d:%02d" % (hours, mins, secs),
    },
    "h:mm:ss.s": {
        "name": "hours:minutes:seconds:deciseconds",
        "round_func": lambda value: round(value, 1),
        "sql_round_func": "ROUND(EXTRACT(EPOCH FROM p_in::INTERVAL)::NUMERIC, 1)",
        "backup_field_if_changing_to": {"h:mm", "h:mm:ss"},
        "format_func": lambda hours, mins, secs: "%d:%02d:%04.1f" % (hours, mins, secs),
    },
    "h:mm:ss.ss": {
        "name": "hours:minutes:seconds:centiseconds",
        "backup_field_if_changing_to": {"h:mm", "h:mm:ss", "h:mm:ss.s"},
        "round_func": lambda value: round(value, 2),
        "sql_round_func": "ROUND(EXTRACT(EPOCH FROM p_in::INTERVAL)::NUMERIC, 2)",
        "format_func": lambda hours, mins, secs: "%d:%02d:%05.2f" % (hours, mins, secs),
    },
    "h:mm:ss.sss": {
        "name": "hours:minutes:seconds:milliseconds",
        "backup_field_if_changing_to": {
            "h:mm",
            "h:mm:ss",
            "h:mm:ss.s",
            "h:mm:ss.ss",
        },
        "round_func": lambda value: round(value, 3),
        "sql_round_func": "ROUND(EXTRACT(EPOCH FROM p_in::INTERVAL)::NUMERIC, 3)",
        "format_func": lambda hours, mins, secs: "%d:%02d:%06.3f" % (hours, mins, secs),
    },
}

# The tokens used in the format strings and their utility functions.
DURATION_FORMAT_TOKENS = {
    "h": {
        "multiplier": 3600,
        "parse_func": int,
        "sql_to_text": "EXTRACT(EPOCH FROM CAST(p_in AS INTERVAL))::INTEGER / 3600",
    },
    "mm": {
        "multiplier": 60,
        "parse_func": int,
        "sql_to_text": "TO_CHAR(EXTRACT(MINUTE FROM CAST(p_in AS INTERVAL)), 'FM00')",
    },
    "ss": {
        "multiplier": 1,
        "parse_func": lambda value: round(float(value), 0),
        "sql_to_text": "TO_CHAR(TRUNC(EXTRACT(SECOND FROM CAST(p_in AS INTERVAL))::NUMERIC, 0), 'FM00')",
    },
    "ss.s": {
        "multiplier": 1,
        "parse_func": lambda value: round(float(value), 1),
        "sql_to_text": "TO_CHAR(TRUNC(EXTRACT(SECOND FROM CAST(p_in AS INTERVAL))::NUMERIC, 1), 'FM00.0')",
    },
    "ss.ss": {
        "multiplier": 1,
        "parse_func": lambda value: round(float(value), 2),
        "sql_to_text": "TO_CHAR(TRUNC(EXTRACT(SECOND FROM CAST(p_in AS INTERVAL))::NUMERIC, 2), 'FM00.00')",
    },
    "ss.sss": {
        "multiplier": 1,
        "parse_func": lambda value: round(float(value), 3),
        "sql_to_text": "TO_CHAR(TRUNC(EXTRACT(SECOND FROM CAST(p_in AS INTERVAL))::NUMERIC, 3), 'FM00.000')",
    },
}
MOST_ACCURATE_DURATION_FORMAT = "h:mm:ss.sss"
MAX_NUMBER_OF_TOKENS_IN_DURATION_FORMAT = len(MOST_ACCURATE_DURATION_FORMAT.split(":"))


# Keep this function in sync with the one in the frontend:
# web-frontend/modules/database/utils/duration.js ->
# guessDurationValueFromString
def parse_formatted_duration(
    formatted_value: str, format: str, strict: bool = False
) -> float:
    """
    Parses a formatted duration string into a number of seconds according to the
    provided format. If the format doesn't match exactly, it will still try to
    parse it as best as possible.

    :param formatted_value: The formatted duration string.
    :param format: The format of the duration string.
    :param strict: If True, the formatted value must match the format exactly or
        a ValueError will be raised. If False, the formatted value can be any
        acceptable format and will be parsed as best as possible.
    :return: The number of seconds.
    :raises ValueError: If the format is invalid.
    """

    if format not in DURATION_FORMATS:
        raise ValueError(f"{format} is not a valid duration format.")

    tokens = format.split(":")
    parts = formatted_value.split(":")
    if len(parts) > len(tokens):
        if strict or len(parts) > MAX_NUMBER_OF_TOKENS_IN_DURATION_FORMAT:
            raise ValueError(
                f"Too many parts in formatted value {formatted_value} for format {format}."
            )
        else:
            # In this case we still want to parse the value as best as possible,
            # so use the most accurate format and round the value later.
            tokens = MOST_ACCURATE_DURATION_FORMAT.split(":")

    total_seconds = 0
    for i, token in enumerate(reversed(tokens)):
        if len(parts) <= i:
            break
        # pick the corresponding part from the end of the list
        part = parts[-(i + 1)]

        token_options = DURATION_FORMAT_TOKENS[token]
        multiplier = token_options["multiplier"]
        parse_func = token_options["parse_func"]

        total_seconds += parse_func(part) * multiplier

    total_seconds = DURATION_FORMATS[format]["round_func"](total_seconds)
    return total_seconds


def convert_duration_input_value_to_timedelta(
    value: Union[int, float, timedelta, str, None], format: str
) -> Optional[timedelta]:
    """
    Converts a raw value for a duration field to a timedelta object. It treats
    the value as a number of seconds if it is an integer or float. If it is a
    string it will parse it using the provided format. Even if the format doesn't
    match exactly, it will still try to parse it as best as possible.

    :param value: The raw value to convert.
    :param format: The format to use when parsing the value if it is a string
        and to round the value to.
    :return: The timedelta object.
    :raises ValueError: If the value is not a valid integer or string according
        to the format.
    :raise OverflowError: If the value is too big to be converted to a timedelta.
    """

    if format not in DURATION_FORMATS:
        raise ValueError(f"{format} is not a valid duration format.")

    if value is None:
        return None
    elif isinstance(value, timedelta):
        return value

    if isinstance(value, (int, float)) and value >= 0:
        total_seconds = value
    elif isinstance(value, str):
        formatted_duration = value
        total_seconds = parse_formatted_duration(formatted_duration, format)
    else:
        raise ValueError(
            "The provided value should be a valid integer or string according to the "
            f"{format} format.",
        )

    round_func = DURATION_FORMATS[format]["round_func"]
    return timedelta(seconds=round_func(total_seconds))


def prepare_duration_value_for_db(
    value, duration_format, default_exc=ValidationError
) -> Optional[timedelta]:
    """
    Prepares a value for a duration field to be stored in the database. It
    converts the value to a timedelta object if it is a valid integer or string
    according to the format. If something is wrong with the value, a
    default_exc is raised with the correct error code and message.

    :param value: The raw value to convert.
    :param duration_format: The format to use when parsing the value if it is a
        string and to round the value to.
    :param default_exc: The exception to raise if something is wrong with the
        value.
    :return: The timedelta object.
    """

    try:
        return convert_duration_input_value_to_timedelta(value, duration_format)
    except ValueError:
        raise default_exc(
            f"The value {value} is not a valid duration.",
            code="invalid",
        )
    except OverflowError:
        raise default_exc(
            f"Value {value} is too large. The maximum is {timedelta.max}.",
            code="invalid",
        )

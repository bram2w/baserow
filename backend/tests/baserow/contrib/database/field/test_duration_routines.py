from datetime import timedelta

import pytest

from baserow.contrib.database.fields.utils.duration import prepare_duration_value_for_db


@pytest.mark.field_duration
@pytest.mark.parametrize(
    "duration_format,user_input,expected_output",
    [
        ("d h", "10:00", timedelta(hours=10)),
        ("d h", "-10:00", timedelta(hours=-10)),
        ("d h mm ss", "1:00:10", timedelta(seconds=3610)),
        ("d h mm ss", "-1:00:10", timedelta(seconds=-3610)),
        ("d h mm ss", -3610, timedelta(seconds=-3610)),
        ("d h mm", -3610, timedelta(seconds=-3600)),
    ],
)
def test_duration_timedelta_to_db(duration_format, user_input, expected_output):
    out = prepare_duration_value_for_db(user_input, duration_format)
    assert out == expected_output, (
        duration_format,
        user_input,
        out,
        expected_output,
    )

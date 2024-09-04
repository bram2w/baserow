from unittest.mock import patch

from django.core.exceptions import ValidationError

import pytest

from baserow.core.formula.validator import ensure_string_or_integer


@pytest.mark.parametrize("value", [0, 1, 10, 100])
@patch("baserow.core.formula.validator.ensure_string")
def test_ensure_string_or_integer_returns_integer(mock_ensure_string, value):
    """
    Ensure that if an integer is passed in, it is returned as an integer.
    """

    result = ensure_string_or_integer(value)
    assert result == value
    mock_ensure_string.assert_not_called()


@pytest.mark.parametrize("value", ["0", "1"])
def test_ensure_string_or_integer_returns_string(value):
    """
    Ensure that if a string is passed in, it is returned.
    """

    result = ensure_string_or_integer(value)
    assert result == value


@pytest.mark.parametrize("value", [None, "", []])
def test_ensure_string_or_integer_raises_if_allow_empty_is_false(value):
    """
    Ensure that if the value is falsey and allow_empty is False, an
    exception is raised.
    """

    with pytest.raises(ValidationError) as e:
        ensure_string_or_integer(value, allow_empty=False)

    assert e.value.message == "A valid String is required."


@pytest.mark.parametrize("value", [None, "", []])
def test_ensure_string_or_integer_returns_empty_string_if_allow_empty_is_true(value):
    """
    Ensure that if the value is falsey and allow_empty is True, an
    empty string is returned.
    """

    result = ensure_string_or_integer(value, allow_empty=True)

    assert result == ""

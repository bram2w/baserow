"""
The assistant validates the formulas it persists. A Builder Markdown text is
stored with the `__markdown__` marker in front of the formula, which is not
part of the formula syntax.
"""

import pytest

from baserow_enterprise.assistant.tools.shared.formula_utils import (
    ensure_valid_formula,
    is_string_literal,
    is_valid_formula,
    wrap_static_string,
)


@pytest.mark.parametrize(
    "formula,expected",
    [
        ("__markdown__'Submit'", True),
        ("__markdown__concat('a', 'b')", True),
        ("__markdown__'Managers' Week'", False),
        ("concat('a', 'b')", True),
        ("'Managers' Week'", False),
    ],
)
def test_is_valid_formula_ignores_text_format_marker(formula, expected):
    assert is_valid_formula(formula) is expected


def test_is_string_literal_ignores_text_format_marker():
    assert is_string_literal("__markdown__'Submit'") is True
    assert is_string_literal("__markdown__concat('a')") is False
    assert wrap_static_string("__markdown__'Submit'") == "__markdown__'Submit'"


@pytest.mark.parametrize(
    "formula,expected",
    [
        # Valid formulas are kept as-is, marker included.
        ("__markdown__'**Submit**'", "__markdown__'**Submit**'"),
        (
            "__markdown__get('data_source.1.field_2')",
            "__markdown__get('data_source.1.field_2')",
        ),
        ("__markdown__", "__markdown__"),
        # An invalid formula is quoted behind the marker, not with it.
        ("__markdown__Managers' Week", "__markdown__'Managers\\' Week'"),
        ("Managers' Week", "'Managers\\' Week'"),
    ],
)
def test_ensure_valid_formula_keeps_text_format_marker(formula, expected):
    assert ensure_valid_formula(formula) == expected

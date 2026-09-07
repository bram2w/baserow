"""
The text format of a Builder text is stored inside the value itself, as a
`__markdown__` marker in front of the formula. These tests cover the helpers and
the core consumers that must ignore the marker.
"""

from unittest.mock import MagicMock

import pytest

from baserow.core.formula import BaserowFormulaObject, resolve_formula
from baserow.core.formula.registries import formula_runtime_function_registry
from baserow.core.formula.text_format import (
    MARKDOWN_PREFIX,
    TEXT_FORMAT_MARKDOWN,
    TEXT_FORMAT_PLAIN,
    add_prefix,
    split_format,
    strip_format,
)
from baserow.core.formula.types import (
    BASEROW_FORMULA_MODE_RAW,
    BASEROW_FORMULA_MODE_SIMPLE,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("__markdown__get('a.b')", (TEXT_FORMAT_MARKDOWN, "get('a.b')")),
        ("__markdown__", (TEXT_FORMAT_MARKDOWN, "")),
        ("get('a.b')", (TEXT_FORMAT_PLAIN, "get('a.b')")),
        # Only a leading marker counts, and a marker inside a literal is text.
        ("'__markdown__**a**'", (TEXT_FORMAT_PLAIN, "'__markdown__**a**'")),
        (" __markdown__a", (TEXT_FORMAT_PLAIN, " __markdown__a")),
        ("", (TEXT_FORMAT_PLAIN, "")),
        (None, (TEXT_FORMAT_PLAIN, None)),
        (5, (TEXT_FORMAT_PLAIN, 5)),
    ],
)
def test_split_format(value, expected):
    assert split_format(value) == expected
    assert strip_format(value) == expected[1]


def test_add_prefix():
    assert add_prefix("get('a.b')") == f"{MARKDOWN_PREFIX}get('a.b')"
    assert add_prefix("get('a.b')", TEXT_FORMAT_MARKDOWN) == "__markdown__get('a.b')"
    assert add_prefix("get('a.b')", TEXT_FORMAT_PLAIN) == "get('a.b')"
    assert add_prefix("", TEXT_FORMAT_MARKDOWN) == "__markdown__"
    assert split_format(add_prefix("x")) == (TEXT_FORMAT_MARKDOWN, "x")


@pytest.mark.parametrize(
    "formula,mode,expected",
    [
        ("'**a**'", BASEROW_FORMULA_MODE_SIMPLE, "**a**"),
        ("__markdown__'**a**'", BASEROW_FORMULA_MODE_SIMPLE, "**a**"),
        ("__markdown__concat('**a**', 'b')", BASEROW_FORMULA_MODE_SIMPLE, "**a**b"),
        # A marker inside the resolved output is just text.
        ("'__markdown__**a**'", BASEROW_FORMULA_MODE_SIMPLE, "__markdown__**a**"),
        ("**a**", BASEROW_FORMULA_MODE_RAW, "**a**"),
        ("__markdown__**a**", BASEROW_FORMULA_MODE_RAW, "**a**"),
        ("", BASEROW_FORMULA_MODE_SIMPLE, ""),
        ("__markdown__", BASEROW_FORMULA_MODE_SIMPLE, ""),
        ("__markdown__", BASEROW_FORMULA_MODE_RAW, ""),
    ],
)
def test_resolve_formula_ignores_the_text_format_marker(formula, mode, expected):
    result = resolve_formula(
        BaserowFormulaObject.create(formula, mode=mode),
        formula_runtime_function_registry,
        MagicMock(),
    )

    assert result == expected

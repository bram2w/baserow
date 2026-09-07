import pytest
from rest_framework.exceptions import ValidationError

from baserow.contrib.builder.application_types import BuilderApplicationType
from baserow.core.formula.exceptions import InvalidRuntimeFormula
from baserow.core.formula.field import BASEROW_FORMULA_VERSION_INITIAL
from baserow.core.formula.serializers import FormulaSerializerField
from baserow.core.formula.types import BASEROW_FORMULA_MODE_SIMPLE


@pytest.mark.parametrize("context", [None, {}, {"application_type": None}])
def test_formula_serializer_field_without_context(context):
    with pytest.raises(ValidationError) as exc:
        field = FormulaSerializerField()
        field._context = context
        field.to_internal_value(
            {
                "formula": "get('data_source.123.field_456')",
                "version": BASEROW_FORMULA_VERSION_INITIAL,
                "mode": BASEROW_FORMULA_MODE_SIMPLE,
            }
        )
    assert str(exc.value.detail[0]) == (
        "The formula serializer field requires "
        "an application type context to validate the formula arguments."
    )


@pytest.mark.parametrize(
    "formula",
    [
        "'__markdown__**a**'",
        "concat('__markdown__', get('data_source.123.field_456'))",
    ],
)
def test_formula_serializer_field_accepts_the_markdown_marker_as_content(formula):
    """
    The Application Builder renders a text surface as Markdown when its
    resolved text starts with `__markdown__`. The marker is content the builder
    types: it lives inside a string literal, so the parser and the validator
    treat the formula like any other.
    """

    field = FormulaSerializerField()
    field._context = {"application_type": BuilderApplicationType}

    result = field.to_internal_value(
        {
            "formula": formula,
            "version": BASEROW_FORMULA_VERSION_INITIAL,
            "mode": BASEROW_FORMULA_MODE_SIMPLE,
        }
    )

    assert result["formula"] == formula


def test_formula_serializer_field_still_rejects_the_marker_as_a_function():
    """
    Outside a string literal the marker is an unknown function, which is why
    it is typed into the text and not prepended to the formula.
    """

    field = FormulaSerializerField()
    field._context = {"application_type": BuilderApplicationType}

    with pytest.raises(InvalidRuntimeFormula, match="__markdown__concat"):
        field.to_internal_value(
            {
                "formula": "__markdown__concat('a')",
                "version": BASEROW_FORMULA_VERSION_INITIAL,
                "mode": BASEROW_FORMULA_MODE_SIMPLE,
            }
        )

import pytest
from rest_framework.exceptions import ValidationError

from baserow.core.formula.field import BASEROW_FORMULA_VERSION_INITIAL
from baserow.core.formula.serializers import FormulaSerializerField
from baserow.core.formula.types import (
    BASEROW_FORMULA_MODE_RAW,
    BASEROW_FORMULA_MODE_SIMPLE,
)


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
        "__markdown__concat('a', 'b')",
        "__markdown__'**a**'",
        # The marker alone is an empty Markdown formula, which is valid.
        "__markdown__",
    ],
)
def test_formula_serializer_field_accepts_text_format_marker(formula):
    from baserow.contrib.builder.application_types import BuilderApplicationType

    field = FormulaSerializerField()
    field._context = {"application_type": BuilderApplicationType}

    result = field.to_internal_value(
        {
            "formula": formula,
            "version": BASEROW_FORMULA_VERSION_INITIAL,
            "mode": BASEROW_FORMULA_MODE_SIMPLE,
        }
    )

    # The stored value keeps the marker, only the validation ignores it.
    assert result["formula"] == formula


def test_formula_serializer_field_accepts_text_format_marker_in_raw_mode():
    field = FormulaSerializerField()
    field._context = {}

    result = field.to_internal_value(
        {
            "formula": "__markdown__**a**",
            "version": BASEROW_FORMULA_VERSION_INITIAL,
            "mode": BASEROW_FORMULA_MODE_RAW,
        }
    )

    assert result["formula"] == "__markdown__**a**"


@pytest.mark.parametrize(
    "formula,code",
    [
        # An unknown data provider is still rejected behind the marker. An
        # unknown function name raises `InvalidRuntimeFormula`, which the field
        # does not translate into a validation error with or without the marker.
        ("__markdown__get('foobar.1')", "invalid_formula_argument"),
        ("__markdown__concat('a'", "invalid"),
    ],
)
def test_formula_serializer_field_still_validates_behind_text_format_marker(
    formula, code
):
    from baserow.contrib.builder.application_types import BuilderApplicationType

    field = FormulaSerializerField()
    field._context = {"application_type": BuilderApplicationType}

    with pytest.raises(ValidationError) as exc:
        field.to_internal_value(
            {
                "formula": formula,
                "version": BASEROW_FORMULA_VERSION_INITIAL,
                "mode": BASEROW_FORMULA_MODE_SIMPLE,
            }
        )

    assert exc.value.detail[0].code == code

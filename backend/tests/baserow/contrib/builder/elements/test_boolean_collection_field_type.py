"""
Test the BooleanCollectionFieldType class.
"""

from unittest.mock import patch

import pytest

from baserow.contrib.builder.elements.collection_field_types import (
    BooleanCollectionFieldType,
)
from baserow.core.formula.serializers import FormulaSerializerField

MODULE_PATH = "baserow.contrib.builder.elements.collection_field_types"


def test_class_properties_are_set():
    """
    Test that the properties of the class are correctly set.

    Ensure the type, allowed_fields, and serializer_field_names properties
    are set to the correct values.
    """

    expected_type = "boolean"
    expected_allowed_fields = ["value"]
    expected_serializer_field_names = ["value"]

    bool_field_type = BooleanCollectionFieldType()

    assert bool_field_type.type == expected_type
    assert bool_field_type.allowed_fields == expected_allowed_fields
    assert bool_field_type.serializer_field_names == expected_serializer_field_names


def test_serializer_field_overrides_returns_expected_value():
    """
    Ensure the serializer_field_overrides() method returns the expected value.
    """

    result = BooleanCollectionFieldType().serializer_field_overrides
    field = result["value"]

    assert type(field) is FormulaSerializerField
    assert field.allow_blank is True
    assert field.default is False
    assert field.required is False
    assert field.help_text == "The boolean value."


@patch(f"{MODULE_PATH}.CollectionFieldType.deserialize_property")
@patch(f"{MODULE_PATH}.import_formula")
def test_deserialize_property_returns_value_from_import_formula(
    mock_import_formula, mock_super_deserialize
):
    """
    Ensure the deserialize_property() method uses import_formula() if the
    prop_name is 'value' and a data_source_id is provided.
    """

    mock_value = "foo"
    mock_import_formula.return_value = mock_value
    prop_name = "value"
    value = "foo"
    id_mapping = {}
    data_source_id = 1

    result = BooleanCollectionFieldType().deserialize_property(
        prop_name, value, id_mapping, {}, data_source_id=data_source_id
    )

    assert result == mock_value
    mock_import_formula.assert_called_once_with(
        value,
        id_mapping,
        data_source_id=data_source_id,
    )
    mock_super_deserialize.assert_not_called()


@patch(f"{MODULE_PATH}.CollectionFieldType.deserialize_property")
@patch(f"{MODULE_PATH}.import_formula")
@pytest.mark.parametrize(
    "prop_name,data_source_id",
    [
        ("", 1),
        (" ", 1),
        ("", None),
        (" ", None),
        # Intentionally misspelt "value"
        ("vallue", 1),
    ],
)
def test_deserialize_property_returns_value_from_super_method(
    mock_import_formula,
    mock_super_deserialize,
    prop_name,
    data_source_id,
):
    """
    Ensure that the value is returned by calling the parent class's
    deserialize_property() method.

    If the prop_name is "value" *and* the data_source_id is not empty, the
    import_formula() is called. All other combinations should cause the
    super method to be called instead.
    """

    mock_value = "'foo'"
    mock_super_deserialize.return_value = mock_value
    value = "'foo'"
    id_mapping = {}

    result = BooleanCollectionFieldType().deserialize_property(
        prop_name,
        value,
        id_mapping,
        {},
        data_source_id=data_source_id,
    )

    assert result == mock_value
    mock_import_formula.assert_not_called()
    mock_super_deserialize.assert_called_once_with(
        prop_name,
        value,
        id_mapping,
        {},
        data_source_id=data_source_id,
    )

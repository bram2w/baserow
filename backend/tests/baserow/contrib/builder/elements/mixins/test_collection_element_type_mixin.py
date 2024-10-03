"""
Test the CollectionElementTypeMixin class.
"""

from unittest.mock import MagicMock

import pytest

from baserow.contrib.builder.elements.mixins import CollectionElementTypeMixin

MODULE_PATH = "baserow.contrib.builder.elements.collection_field_types"


@pytest.mark.parametrize(
    "schema_property",
    [
        "field_123",
        None,
    ],
)
def test_import_context_addition_sets_schema_property(schema_property):
    """
    Test the import_context_addition() method.

    Ensure that the schema_property is set when the element has a schema property.
    """

    data_source_id = 100

    mock_element = MagicMock()
    mock_element.schema_property = schema_property
    mock_element.data_source_id = data_source_id

    result = CollectionElementTypeMixin().import_context_addition(mock_element)

    assert result["data_source_id"] == data_source_id
    if schema_property:
        assert result["schema_property"] == schema_property
    else:
        assert "schema_property" not in result

import pytest

from baserow.contrib.builder.elements.element_types import RecordSelectorElementType


@pytest.mark.django_db
def test_record_selector_element_extract_formula_properties(data_fixture):
    user = data_fixture.create_user()
    element_type = RecordSelectorElementType()

    # If the record selector has no data source, then the formula properties are empty
    element = data_fixture.create_builder_record_selector_element(data_source=None)
    properties = element_type.extract_formula_properties(element, {})
    assert properties == {}

    # If the record selector has a data source *without* a table then the
    # formula properties just include "id"
    data_source = data_fixture.create_builder_local_baserow_list_rows_data_source()
    element = data_fixture.create_builder_record_selector_element(
        data_source=data_source
    )
    properties = element_type.extract_formula_properties(element, {})
    assert properties == {element.data_source.service_id: ["id"]}

    # If the record selector has a data source *with* a table that does not
    # define a name property, then the formula properties just include "id"
    table = data_fixture.create_database_table(user=user)
    data_source = data_fixture.create_builder_local_baserow_list_rows_data_source(
        table=table
    )
    element = data_fixture.create_builder_record_selector_element(
        data_source=data_source
    )
    properties = element_type.extract_formula_properties(element, {})
    assert properties == {data_source.service_id: ["id"]}

    # If the record selector has a data source whose table defines a name property
    # then the formula properties includes the "id" and the field name
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(name="Name", table=table, primary=True)
    data_source = data_fixture.create_builder_local_baserow_list_rows_data_source(
        table=table
    )
    element = data_fixture.create_builder_record_selector_element(
        data_source=data_source
    )
    properties = element_type.extract_formula_properties(element, {})
    assert properties == {data_source.service_id: ["id", field.db_column]}

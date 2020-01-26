import pytest


@pytest.mark.django_db
def test_model_class_name(data_fixture):
    field_1 = data_fixture.create_text_field(name='Some test table')
    assert field_1.model_attribute_name == 'some_test_table'

    field_2 = data_fixture.create_text_field(name='3 Some test @ table')
    assert field_2.model_attribute_name == 'field_3_some_test_table'

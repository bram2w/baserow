import pytest

from django.db import models

from baserow.contrib.database.table.models import Table


@pytest.mark.django_db
def test_group_user_get_next_order(data_fixture):
    database = data_fixture.create_database_application()
    database_2 = data_fixture.create_database_application()
    data_fixture.create_database_table(order=1, database=database)
    data_fixture.create_database_table(order=2, database=database)
    data_fixture.create_database_table(order=10, database=database_2)

    assert Table.get_last_order(database) == 3
    assert Table.get_last_order(database_2) == 11


@pytest.mark.django_db
def test_model_class_name(data_fixture):
    table_1 = data_fixture.create_database_table(name='Some test table')
    assert table_1.model_class_name == 'SomeTestTable'

    table_2 = data_fixture.create_database_table(name='3 Some test @ table')
    assert table_2.model_class_name == 'Table3SomeTestTable'


@pytest.mark.django_db
def test_get_table_model(data_fixture):
    table = data_fixture.create_database_table(name='Cars')
    text_field = data_fixture.create_text_field(table=table, order=0, name='Color',
                                                text_default='white')
    number_field = data_fixture.create_number_field(table=table, order=1,
                                                    name='Horsepower')
    boolean_field = data_fixture.create_boolean_field(table=table, order=2,
                                                      name='For sale')

    model = table.get_model(attribute_names=True)
    assert model._generated_table_model
    assert model._meta.db_table == f'database_table_{table.id}'
    assert len(model._meta.get_fields()) == 4

    color_field = model._meta.get_field('color')
    horsepower_field = model._meta.get_field('horsepower')
    for_sale_field = model._meta.get_field('for_sale')

    assert isinstance(color_field, models.TextField)
    assert color_field.verbose_name == 'Color'
    assert color_field.db_column == f'field_{text_field.id}'
    assert color_field.default == 'white'
    assert color_field.null

    assert isinstance(horsepower_field, models.IntegerField)
    assert horsepower_field.verbose_name == 'Horsepower'
    assert horsepower_field.db_column == f'field_{number_field.id}'
    assert horsepower_field.null

    assert isinstance(for_sale_field, models.BooleanField)
    assert for_sale_field.verbose_name == 'For sale'
    assert for_sale_field.db_column == f'field_{boolean_field.id}'
    assert not for_sale_field.default

    table_2 = data_fixture.create_database_table(name='House')
    data_fixture.create_number_field(table=table_2, order=0, name='Sale price',
                                     number_type='DECIMAL', number_decimal_places=3,
                                     number_negative=True)

    model = table_2.get_model(attribute_names=True)
    sale_price_field = model._meta.get_field('sale_price')
    assert isinstance(sale_price_field, models.DecimalField)
    assert sale_price_field.decimal_places == 3
    assert sale_price_field.null

    model_2 = table.get_model(fields=[number_field], field_ids=[text_field.id],
                              attribute_names=True)
    assert len(model_2._meta.get_fields()) == 3

    color_field = model_2._meta.get_field('color')
    assert color_field
    assert color_field.db_column == f'field_{text_field.id}'

    horsepower_field = model_2._meta.get_field('horsepower')
    assert horsepower_field
    assert horsepower_field.db_column == f'field_{number_field.id}'

    model_3 = table.get_model()
    assert model_3._meta.db_table == f'database_table_{table.id}'
    assert len(model_3._meta.get_fields()) == 4

    field_1 = model_3._meta.get_field(f'field_{text_field.id}')
    assert isinstance(field_1, models.TextField)
    assert field_1.db_column == f'field_{text_field.id}'

    field_2 = model_3._meta.get_field(f'field_{number_field.id}')
    assert isinstance(field_2, models.IntegerField)
    assert field_2.db_column == f'field_{number_field.id}'

    field_3 = model_3._meta.get_field(f'field_{boolean_field.id}')
    assert isinstance(field_3, models.BooleanField)
    assert field_3.db_column == f'field_{boolean_field.id}'

    text_field_2 = data_fixture.create_text_field(table=table, order=3, name='Color',
                                                  text_default='orange')
    model = table.get_model(attribute_names=True)
    field_names = [f.name for f in model._meta.get_fields()]
    assert len(field_names) == 5
    assert f'{text_field.model_attribute_name}_field_{text_field.id}' in field_names
    assert f'{text_field_2.model_attribute_name}_field_{text_field.id}' in field_names

    # Test if the fields are also returns if requested.
    model = table.get_model()
    fields = model._field_objects
    assert len(fields.items()) == 4

    assert fields[text_field.id]['field'].id == text_field.id
    assert fields[text_field.id]['type'].type == 'text'
    assert fields[text_field.id]['name'] == f'field_{text_field.id}'

    assert fields[number_field.id]['field'].id == number_field.id
    assert fields[number_field.id]['type'].type == 'number'
    assert fields[number_field.id]['name'] == f'field_{number_field.id}'

    assert fields[boolean_field.id]['field'].id == boolean_field.id
    assert fields[boolean_field.id]['type'].type == 'boolean'
    assert fields[boolean_field.id]['name'] == f'field_{boolean_field.id}'

    assert fields[text_field_2.id]['field'].id == text_field_2.id
    assert fields[text_field_2.id]['type'].type == 'text'
    assert fields[text_field_2.id]['name'] == f'field_{text_field_2.id}'

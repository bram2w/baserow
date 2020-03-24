import pytest

from baserow.contrib.database.api.v0.rows.serializers import get_row_serializer_class


@pytest.mark.django_db
def test_get_table_serializer(data_fixture):
    table = data_fixture.create_database_table(name='Cars')
    table_2 = data_fixture.create_database_table()
    data_fixture.create_text_field(table=table, order=0, name='Color',
                                   text_default='white')
    data_fixture.create_number_field(table=table, order=1, name='Horsepower')
    data_fixture.create_boolean_field(table=table, order=2, name='For sale')

    model = table.get_model(attribute_names=True)
    serializer_class = get_row_serializer_class(model=model)

    # text field
    serializer_instance = serializer_class(data={'color': 'Green'})
    assert serializer_instance.is_valid()
    assert serializer_instance.data == {'color': 'Green'}

    serializer_instance = serializer_class(data={'color': 123})
    assert serializer_instance.is_valid()
    assert serializer_instance.data == {'color': '123'}

    serializer_instance = serializer_class(data={'color': None})
    assert not serializer_instance.is_valid()
    assert len(serializer_instance.errors['color']) == 1

    # number field
    serializer_instance = serializer_class(data={'horsepower': 120})
    assert serializer_instance.is_valid()
    assert serializer_instance.data == {'horsepower': 120}

    serializer_instance = serializer_class(data={'horsepower': 'abc'})
    assert not serializer_instance.is_valid()
    assert len(serializer_instance.errors['horsepower']) == 1

    serializer_instance = serializer_class(data={'horsepower': -1})
    assert not serializer_instance.is_valid()
    assert len(serializer_instance.errors['horsepower']) == 1

    # boolean field
    serializer_instance = serializer_class(data={'for_sale': True})
    assert serializer_instance.is_valid()
    assert serializer_instance.data == {'for_sale': True}

    serializer_instance = serializer_class(data={'for_sale': None})
    assert not serializer_instance.is_valid()
    assert len(serializer_instance.errors['for_sale']) == 1

    # boolean field
    serializer_instance = serializer_class(data={'NOT_EXISTING': True})
    assert serializer_instance.is_valid()
    assert serializer_instance.data == {}

    # all fields
    serializer_instance = serializer_class(data={
        'color': 'green',
        'horsepower': 120,
        'for_sale': True
    })
    assert serializer_instance.is_valid()
    assert serializer_instance.data == {
        'color': 'green',
        'horsepower': 120,
        'for_sale': True
    }

    price_field = data_fixture.create_number_field(
        table=table_2, order=0, name='Sale price', number_type='DECIMAL',
        number_decimal_places=3, number_negative=True
    )
    model = table.get_model(fields=[price_field], field_ids=[])
    serializer_class = get_row_serializer_class(model=model)

    serializer_instance = serializer_class(data={f'field_{price_field.id}': 12.22})
    assert serializer_instance.is_valid()
    assert serializer_instance.data == {f'field_{price_field.id}': '12.220'}

    serializer_instance = serializer_class(data={f'field_{price_field.id}': -10.02})
    assert serializer_instance.is_valid()
    assert serializer_instance.data == {f'field_{price_field.id}': '-10.020'}

    serializer_instance = serializer_class(data={f'field_{price_field.id}': 'abc'})
    assert not serializer_instance.is_valid()
    assert len(serializer_instance.errors[f'field_{price_field.id}']) == 1

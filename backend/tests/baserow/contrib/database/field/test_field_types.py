import pytest

from faker import Faker

from decimal import Decimal

from baserow.contrib.database.fields.models import LongTextField
from baserow.contrib.database.fields.handler import FieldHandler


@pytest.mark.django_db
@pytest.mark.parametrize(
    "expected,field_kwargs",
    [
        (
            [100, 100, 101, 0, 0, 0, None, None, None, None, None],
            {'number_type': 'INTEGER', 'number_negative': False}
        ),
        (
            [100, 100, 101, -100, -100, -101, None, None, None, None, None],
            {'number_type': 'INTEGER', 'number_negative': True}
        ),
        (
            [
                Decimal('100.0'), Decimal('100.2'), Decimal('100.6'), Decimal('0.0'),
                Decimal('0.0'), Decimal('0.0'), None, None, None, None, None
            ],
            {
                'number_type': 'DECIMAL', 'number_negative': False,
                'number_decimal_places': 1
            }
        ),
        (
            [
                Decimal('100.000'), Decimal('100.220'), Decimal('100.600'),
                Decimal('-100.0'), Decimal('-100.220'), Decimal('-100.600'), None, None,
                None, None, None
            ],
            {
                'number_type': 'DECIMAL', 'number_negative': True,
                'number_decimal_places': 3
            }
        )
    ]
)
def test_alter_number_field_column_type(expected, field_kwargs, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table, order=1)

    handler = FieldHandler()
    field = handler.update_field(user=user, field=field, name='Text field')

    model = table.get_model()
    model.objects.create(**{f'field_{field.id}': '100'})
    model.objects.create(**{f'field_{field.id}': '100.22'})
    model.objects.create(**{f'field_{field.id}': '100.59999'})
    model.objects.create(**{f'field_{field.id}': '-100'})
    model.objects.create(**{f'field_{field.id}': '-100.22'})
    model.objects.create(**{f'field_{field.id}': '-100.5999'})
    model.objects.create(**{f'field_{field.id}': '100.59.99'})
    model.objects.create(**{f'field_{field.id}': '-100.59.99'})
    model.objects.create(**{f'field_{field.id}': '100TEST100.10'})
    model.objects.create(**{f'field_{field.id}': '!@#$%%^^&&^^%$$'})
    model.objects.create(**{f'field_{field.id}': '!@#$%%^^5.2&&^^%$$'})

    # Change the field type to a number and test if the values have been changed.
    field = handler.update_field(user=user, field=field, new_type_name='number',
                                 **field_kwargs)

    model = table.get_model()
    rows = model.objects.all()
    for index, row in enumerate(rows):
        assert getattr(row, f'field_{field.id}') == expected[index]


@pytest.mark.django_db
def test_alter_number_field_column_type_negative(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    number_field = data_fixture.create_number_field(table=table, order=1,
                                                    number_negative=True)
    decimal_field = data_fixture.create_number_field(table=table, order=2,
                                                     number_type='DECIMAL',
                                                     number_negative=True,
                                                     number_decimal_places=2)

    model = table.get_model()
    model.objects.create(**{
        f'field_{number_field.id}': -10,
        f'field_{decimal_field.id}': Decimal('-10.10')
    })

    handler = FieldHandler()
    number_field = handler.update_field(user=user, field=number_field,
                                        number_negative=False)
    decimal_field = handler.update_field(user=user, field=decimal_field,
                                         number_negative=False)

    model = table.get_model()
    rows = model.objects.all()
    assert getattr(rows[0], f'field_{number_field.id}') == 0
    assert getattr(rows[0], f'field_{decimal_field.id}') == 0.00


@pytest.mark.django_db
def test_alter_boolean_field_column_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table, order=1)

    handler = FieldHandler()
    field = handler.update_field(user=user, field=field, name='Text field')

    model = table.get_model()
    mapping = {
        '1': True,
        't': True,
        'y': True,
        'yes': True,
        'on': True,
        'YES': True,

        '': False,
        'f': False,
        'n': False,
        'false': False,
        'off': False,
        'Random text': False,
    }

    for value in mapping.keys():
        model.objects.create(**{f'field_{field.id}': value})

    # Change the field type to a number and test if the values have been changed.
    field = handler.update_field(user=user, field=field, new_type_name='boolean')

    model = table.get_model()
    rows = model.objects.all()

    for index, value in enumerate(mapping.values()):
        assert getattr(rows[index], f'field_{field.id}') == value


@pytest.mark.django_db
def test_long_text_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table, order=1, name='name')

    handler = FieldHandler()
    handler.create_field(user=user, table=table, type_name='long_text',
                         name='description')
    field = handler.update_field(user=user, field=field, new_type_name='long_text')

    assert len(LongTextField.objects.all()) == 2

    fake = Faker()
    text = fake.text()
    model = table.get_model(attribute_names=True)
    row = model.objects.create(description=text, name='Test')

    assert row.description == text
    assert row.name == 'Test'

    handler.delete_field(user=user, field=field)
    assert len(LongTextField.objects.all()) == 1

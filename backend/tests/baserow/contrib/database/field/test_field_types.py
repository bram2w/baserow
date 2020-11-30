import pytest
import json
from pytz import timezone
from datetime import date
from faker import Faker
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware, datetime

from baserow.core.user_files.exceptions import (
    InvalidUserFileNameError, UserFileDoesNotExist
)
from baserow.contrib.database.fields.field_types import DateFieldType
from baserow.contrib.database.fields.models import (
    LongTextField, URLField, DateField, EmailField, FileField
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler


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


@pytest.mark.django_db
def test_url_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_database_table(user=user, database=table.database)
    field = data_fixture.create_text_field(table=table, order=1, name='name')

    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_2 = field_handler.create_field(user=user, table=table, type_name='url',
                                         name='url')
    number = field_handler.create_field(user=user, table=table, type_name='number',
                                        name='number')

    assert len(URLField.objects.all()) == 1
    model = table.get_model(attribute_names=True)

    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={
            'url': 'invalid_url'
        }, model=model)

    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={
            'url': 'httpss'
        }, model=model)

    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={
            'url': 'httpss'
        }, model=model)

    row_handler.create_row(user=user, table=table, values={
        'name': 'http://test.nl',
        'url': 'https://baserow.io',
        'number': 5
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'name': 'http;//',
        'url': 'http://localhost',
        'number': 10
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'name': 'bram@test.nl',
        'url': 'http://www.baserow.io'
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'name': 'NOT A URL',
        'url': 'http://www.baserow.io/blog/building-a-database'
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'name': 'ftps://www.complex.website.com?querystring=test&something=else',
        'url': ''
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'url': None,
    }, model=model)
    row_handler.create_row(user=user, table=table, values={}, model=model)

    # Convert to text field to a url field so we can check how the conversion of values
    # went.
    field_handler.update_field(user=user, field=field, new_type_name='url')
    field_handler.update_field(user=user, field=number, new_type_name='url')

    model = table.get_model(attribute_names=True)
    rows = model.objects.all()

    assert rows[0].name == 'http://test.nl'
    assert rows[0].url == 'https://baserow.io'
    assert rows[0].number == ''

    assert rows[1].name == ''
    assert rows[1].url == 'http://localhost'
    assert rows[1].number == ''

    assert rows[2].name == ''
    assert rows[2].url == 'http://www.baserow.io'
    assert rows[2].number == ''

    assert rows[3].name == ''
    assert rows[3].url == 'http://www.baserow.io/blog/building-a-database'
    assert rows[3].number == ''

    assert (
        rows[4].name == 'ftps://www.complex.website.com?querystring=test&something=else'
    )
    assert rows[4].url == ''
    assert rows[4].number == ''

    assert rows[5].name == ''
    assert rows[5].url == ''
    assert rows[5].number == ''

    assert rows[6].name == ''
    assert rows[6].url == ''
    assert rows[6].number == ''

    field_handler.delete_field(user=user, field=field_2)
    assert len(URLField.objects.all()) == 2


@pytest.mark.django_db
def test_date_field_type_prepare_value(data_fixture):
    d = DateFieldType()

    f = data_fixture.create_date_field(date_include_time=True)
    amsterdam = timezone('Europe/Amsterdam')
    utc = timezone('UTC')
    expected_date = make_aware(datetime(2020, 4, 10, 0, 0, 0), utc)
    expected_datetime = make_aware(datetime(2020, 4, 10, 12, 30, 30), utc)

    with pytest.raises(ValidationError):
        assert d.prepare_value_for_db(f, 'TEST')

    assert d.prepare_value_for_db(f, None) is None

    unprepared_datetime = make_aware(datetime(2020, 4, 10, 14, 30, 30), amsterdam)
    assert d.prepare_value_for_db(f, unprepared_datetime) == expected_datetime

    unprepared_datetime = make_aware(datetime(2020, 4, 10, 12, 30, 30), utc)
    assert d.prepare_value_for_db(f, unprepared_datetime) == expected_datetime

    unprepared_datetime = datetime(2020, 4, 10, 12, 30, 30)
    assert d.prepare_value_for_db(f, unprepared_datetime) == expected_datetime

    unprepared_date = date(2020, 4, 10)
    assert d.prepare_value_for_db(f, unprepared_date) == expected_date

    assert d.prepare_value_for_db(f, '2020-04-10') == expected_date
    assert d.prepare_value_for_db(f, '2020-04-11') != expected_date
    assert d.prepare_value_for_db(f, '2020-04-10 12:30:30') == expected_datetime
    assert d.prepare_value_for_db(f, '2020-04-10 00:30:30 PM') == expected_datetime

    f = data_fixture.create_date_field(date_include_time=False)
    expected_date = date(2020, 4, 10)

    unprepared_datetime = datetime(2020, 4, 10, 14, 30, 30)
    assert d.prepare_value_for_db(f, unprepared_datetime) == expected_date

    unprepared_datetime = make_aware(datetime(2020, 4, 10, 14, 30, 30), amsterdam)
    assert d.prepare_value_for_db(f, unprepared_datetime) == expected_date

    assert d.prepare_value_for_db(f, '2020-04-10') == expected_date
    assert d.prepare_value_for_db(f, '2020-04-11') != expected_date
    assert d.prepare_value_for_db(f, '2020-04-10 12:30:30') == expected_date
    assert d.prepare_value_for_db(f, '2020-04-10 00:30:30 PM') == expected_date


@pytest.mark.django_db
def test_date_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    amsterdam = timezone('Europe/Amsterdam')
    utc = timezone('utc')

    date_field_1 = field_handler.create_field(user=user, table=table, type_name='date',
                                              name='Date')
    date_field_2 = field_handler.create_field(user=user, table=table, type_name='date',
                                              name='Datetime', date_include_time=True)

    assert date_field_1.date_include_time is False
    assert date_field_2.date_include_time is True
    assert len(DateField.objects.all()) == 2

    model = table.get_model(attribute_names=True)

    row = row_handler.create_row(user=user, table=table, values={}, model=model)
    assert row.date is None
    assert row.datetime is None

    row = row_handler.create_row(user=user, table=table, values={
        'date': '2020-4-1',
        'datetime': '2020-4-1 12:30:30'
    }, model=model)
    row.refresh_from_db()
    assert row.date == date(2020, 4, 1)
    assert row.datetime == datetime(2020, 4, 1, 12, 30, 30, tzinfo=utc)

    row = row_handler.create_row(user=user, table=table, values={
        'datetime': make_aware(datetime(2020, 4, 1, 12, 30, 30), amsterdam)
    }, model=model)
    row.refresh_from_db()
    assert row.date is None
    assert row.datetime == datetime(2020, 4, 1, 10, 30, 30, tzinfo=timezone('UTC'))

    date_field_1 = field_handler.update_field(user=user, field=date_field_1,
                                              date_include_time=True)
    date_field_2 = field_handler.update_field(user=user, field=date_field_2,
                                              date_include_time=False)

    assert date_field_1.date_include_time is True
    assert date_field_2.date_include_time is False

    model = table.get_model(attribute_names=True)
    rows = model.objects.all()

    assert rows[0].date is None
    assert rows[0].datetime is None
    assert rows[1].date == datetime(2020, 4, 1, tzinfo=timezone('UTC'))
    assert rows[1].datetime == date(2020, 4, 1)
    assert rows[2].date is None
    assert rows[2].datetime == date(2020, 4, 1)

    field_handler.delete_field(user=user, field=date_field_1)
    field_handler.delete_field(user=user, field=date_field_2)

    assert len(DateField.objects.all()) == 0


@pytest.mark.django_db
def test_email_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_database_table(user=user, database=table.database)
    field = data_fixture.create_text_field(table=table, order=1, name='name')

    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_2 = field_handler.create_field(user=user, table=table, type_name='email',
                                         name='email')
    number = field_handler.create_field(user=user, table=table, type_name='number',
                                        name='number')

    assert len(EmailField.objects.all()) == 1
    model = table.get_model(attribute_names=True)

    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={
            'email': 'invalid_email'
        }, model=model)

    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={
            'email': 'invalid@email'
        }, model=model)

    row_handler.create_row(user=user, table=table, values={
        'name': 'a.very.STRANGE@email.address.coM',
        'email': 'test@test.nl',
        'number': 5
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'name': 'someuser',
        'email': 'some@user.com',
        'number': 10
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'name': 'http://www.baserow.io',
        'email': 'bram@test.nl'
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'name': 'NOT AN EMAIL',
        'email': 'something@example.com'
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'name': 'testing@nowhere.org',
        'email': ''
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'email': None,
    }, model=model)
    row_handler.create_row(user=user, table=table, values={}, model=model)

    # Convert the text field to a url field so we can check how the conversion of
    # values went.
    field_handler.update_field(user=user, field=field, new_type_name='email')
    field_handler.update_field(user=user, field=number, new_type_name='email')

    model = table.get_model(attribute_names=True)
    rows = model.objects.all()

    assert rows[0].name == 'a.very.STRANGE@email.address.coM'
    assert rows[0].email == 'test@test.nl'
    assert rows[0].number == ''

    assert rows[1].name == ''
    assert rows[1].email == 'some@user.com'
    assert rows[1].number == ''

    assert rows[2].name == ''
    assert rows[2].email == 'bram@test.nl'
    assert rows[2].number == ''

    assert rows[3].name == ''
    assert rows[3].email == 'something@example.com'
    assert rows[3].number == ''

    assert rows[4].name == 'testing@nowhere.org'
    assert rows[4].email == ''
    assert rows[4].number == ''

    assert rows[5].name == ''
    assert rows[5].email == ''
    assert rows[5].number == ''

    assert rows[6].name == ''
    assert rows[6].email == ''
    assert rows[6].number == ''

    field_handler.delete_field(user=user, field=field_2)
    assert len(EmailField.objects.all()) == 2


@pytest.mark.django_db
def test_file_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    user_file_1 = data_fixture.create_user_file()
    user_file_2 = data_fixture.create_user_file()
    user_file_3 = data_fixture.create_user_file()

    field_handler = FieldHandler()
    row_handler = RowHandler()

    file = field_handler.create_field(user=user, table=table, type_name='file',
                                      name='File')

    assert FileField.objects.all().count() == 1
    model = table.get_model(attribute_names=True)

    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={
            'file': 'not_a_json'
        }, model=model)

    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={
            'file': {}
        }, model=model)

    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={
            'file': [{'no_name': 'test'}]
        }, model=model)

    with pytest.raises(InvalidUserFileNameError):
        row_handler.create_row(user=user, table=table, values={
            'file': [{'name': 'wrongfilename.jpg'}]
        }, model=model)

    with pytest.raises(UserFileDoesNotExist):
        row_handler.create_row(user=user, table=table, values={
            'file': [{'name': 'file_name.jpg'}]
        }, model=model)

    row = row_handler.create_row(user=user, table=table, values={
        'file': [{'name': user_file_1.name}]
    }, model=model)
    assert row.file[0]['visible_name'] == user_file_1.original_name
    del row.file[0]['visible_name']
    assert row.file[0] == user_file_1.serialize()

    row = row_handler.create_row(user=user, table=table, values={
        'file': [
            {'name': user_file_2.name},
            {'name': user_file_1.name},
            {'name': user_file_1.name}
        ]
    }, model=model)
    assert row.file[0]['visible_name'] == user_file_2.original_name
    assert row.file[1]['visible_name'] == user_file_1.original_name
    assert row.file[2]['visible_name'] == user_file_1.original_name
    del row.file[0]['visible_name']
    del row.file[1]['visible_name']
    del row.file[2]['visible_name']
    assert row.file[0] == user_file_2.serialize()
    assert row.file[1] == user_file_1.serialize()
    assert row.file[2] == user_file_1.serialize()

    row = row_handler.create_row(user=user, table=table, values={
        'file': [
            {'name': user_file_1.name},
            {'name': user_file_3.name},
            {'name': user_file_2.name}
        ]
    }, model=model)
    assert row.file[0]['visible_name'] == user_file_1.original_name
    assert row.file[1]['visible_name'] == user_file_3.original_name
    assert row.file[2]['visible_name'] == user_file_2.original_name
    del row.file[0]['visible_name']
    del row.file[1]['visible_name']
    del row.file[2]['visible_name']
    assert row.file[0] == user_file_1.serialize()
    assert row.file[1] == user_file_3.serialize()
    assert row.file[2] == user_file_2.serialize()

    row = row_handler.update_row(user=user, table=table, row_id=row.id, values={
        'file': [
            {'name': user_file_1.name, 'visible_name': 'not_original.jpg'},
        ]
    }, model=model)
    assert row.file[0]['visible_name'] == 'not_original.jpg'
    del row.file[0]['visible_name']
    assert row.file[0] == user_file_1.serialize()

    assert model.objects.all().count() == 3
    field_handler.delete_field(user=user, field=file)
    assert FileField.objects.all().count() == 0
    model.objects.all().delete()

    text = field_handler.create_field(user=user, table=table, type_name='text',
                                      name='Text')
    model = table.get_model(attribute_names=True)

    row = row_handler.create_row(user=user, table=table, values={
        'text': 'Some random text'
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'text': '["Not compatible"]'
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'text': json.dumps(user_file_1.serialize())
    }, model=model)

    file = field_handler.update_field(user=user, table=table, field=text,
                                      new_type_name='file', name='File')
    model = table.get_model(attribute_names=True)
    results = model.objects.all()
    assert results[0].file == []
    assert results[1].file == []
    assert results[2].file == []

    row_handler.update_row(user=user, table=table, row_id=row.id, values={
        'file': [
            {'name': user_file_1.name, 'visible_name': 'not_original.jpg'},
        ]
    }, model=model)

    field_handler.update_field(user=user, table=table, field=file,
                               new_type_name='text', name='text')
    model = table.get_model(attribute_names=True)
    results = model.objects.all()
    assert results[0].text is None
    assert results[1].text is None
    assert results[2].text is None

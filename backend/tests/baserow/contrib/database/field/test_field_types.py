import pytest
import json

from django.test.utils import override_settings
from faker import Faker

from django.core.exceptions import ValidationError

from baserow.contrib.database.fields.field_types import PhoneNumberFieldType
from baserow.core.user_files.exceptions import (
    InvalidUserFileNameError, UserFileDoesNotExist
)
from baserow.contrib.database.fields.models import (
    LongTextField, URLField, EmailField, FileField, PhoneNumberField
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
def test_import_export_text_field(data_fixture):
    id_mapping = {}

    text_field = data_fixture.create_text_field(
        name='Text name',
        text_default='Text default'
    )
    text_field_type = field_type_registry.get_by_model(text_field)
    text_serialized = text_field_type.export_serialized(text_field)
    text_field_imported = text_field_type.import_serialized(
        text_field.table,
        text_serialized,
        id_mapping
    )
    assert text_field.id != text_field_imported.id
    assert text_field.name == text_field_imported.name
    assert text_field.order == text_field_imported.order
    assert text_field.primary == text_field_imported.primary
    assert text_field.text_default == text_field_imported.text_default
    assert id_mapping['database_fields'][text_field.id] == text_field_imported.id


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


@pytest.mark.django_db
@override_settings(debug=True)
def test_phone_number_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_database_table(user=user, database=table.database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    text_field = field_handler.create_field(user=user, table=table,
                                            order=1,
                                            type_name='text',
                                            name='name')
    phone_number_field = field_handler.create_field(user=user, table=table,
                                                    type_name='phone_number',
                                                    name='phonenumber')
    email_field = field_handler.create_field(user=user, table=table,
                                             type_name='email',
                                             name='email')
    number_field = data_fixture.create_number_field(table=table, order=1,
                                                    number_negative=True, name="number")

    assert len(PhoneNumberField.objects.all()) == 1
    model = table.get_model(attribute_names=True)

    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={
            'phonenumber': 'invalid phone number'
        }, model=model)

    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={
            'phonenumber': 'Phone: 2312321 2349432 '
        }, model=model)
    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={
            'phonenumber': '1' * (PhoneNumberFieldType.MAX_PHONE_NUMBER_LENGTH+1)
        }, model=model)

    max_length_phone_number = '1' * PhoneNumberFieldType.MAX_PHONE_NUMBER_LENGTH
    row_handler.create_row(user=user, table=table, values={
        'name': '+45(1424) 322314 324234',
        'phonenumber': max_length_phone_number,
        'number': 1234534532,
        'email': 'a_valid_email_to_be_blanked_after_conversion@email.com'
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'name': 'some text which should be blanked out after conversion',
        'phonenumber': '1234567890 NnXx,+._*()#=;/ -',
        'number': 0
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'name': max_length_phone_number,
        'phonenumber': '',
        'number': -10230450,
    }, model=model)
    row_handler.create_row(user=user, table=table, values={
        'phonenumber': None,
        'name': '1' * (PhoneNumberFieldType.MAX_PHONE_NUMBER_LENGTH+1)

    }, model=model)
    row_handler.create_row(user=user, table=table, values={}, model=model)

    # No actual database type change occurs here as a phone number field is also a text
    # field. Instead the after_update hook is being used to clear out invalid
    # phone numbers.
    field_handler.update_field(user=user, field=text_field,
                               new_type_name='phone_number')

    field_handler.update_field(user=user, field=number_field,
                               new_type_name='phone_number')
    field_handler.update_field(user=user, field=email_field,
                               new_type_name='phone_number')

    model = table.get_model(attribute_names=True)
    rows = model.objects.all()

    assert rows[0].name == '+45(1424) 322314 324234'
    assert rows[0].phonenumber == max_length_phone_number
    assert rows[0].number == '1234534532'
    assert rows[0].email == ''

    assert rows[1].name == ''
    assert rows[1].phonenumber == '1234567890 NnXx,+._*()#=;/ -'
    assert rows[1].number == '0'

    assert rows[2].name == max_length_phone_number
    assert rows[2].phonenumber == ''
    assert rows[2].number == '-10230450'

    assert rows[3].name == ''
    assert rows[3].phonenumber == ''
    assert rows[3].number == ''

    field_handler.delete_field(user=user, field=phone_number_field)
    assert len(PhoneNumberField.objects.all()) == 3

import pytest
from django.core.exceptions import ValidationError
from django.test.utils import override_settings
from faker import Faker

from baserow.contrib.database.fields.field_types import (
    PhoneNumberFieldType,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import (
    LongTextField,
    URLField,
    EmailField,
    PhoneNumberField,
)
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.handler import RowHandler
from tests.test_utils import setup_interesting_test_table


@pytest.mark.django_db
def test_import_export_text_field(data_fixture):
    id_mapping = {}

    text_field = data_fixture.create_text_field(
        name="Text name", text_default="Text default"
    )
    text_field_type = field_type_registry.get_by_model(text_field)
    text_serialized = text_field_type.export_serialized(text_field)
    text_field_imported = text_field_type.import_serialized(
        text_field.table, text_serialized, id_mapping
    )
    assert text_field.id != text_field_imported.id
    assert text_field.name == text_field_imported.name
    assert text_field.order == text_field_imported.order
    assert text_field.primary == text_field_imported.primary
    assert text_field.text_default == text_field_imported.text_default
    assert id_mapping["database_fields"][text_field.id] == text_field_imported.id


@pytest.mark.django_db
def test_long_text_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table, order=1, name="name")

    handler = FieldHandler()
    handler.create_field(
        user=user, table=table, type_name="long_text", name="description"
    )
    field = handler.update_field(user=user, field=field, new_type_name="long_text")

    assert len(LongTextField.objects.all()) == 2

    fake = Faker()
    text = fake.text()
    model = table.get_model(attribute_names=True)
    row = model.objects.create(description=text, name="Test")

    assert row.description == text
    assert row.name == "Test"

    handler.delete_field(user=user, field=field)
    assert len(LongTextField.objects.all()) == 1


@pytest.mark.django_db
def test_valid_url(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_database_table(user=user, database=table.database)
    field = data_fixture.create_text_field(table=table, order=1, name="name")
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_handler.create_field(user=user, table=table, type_name="url", name="URL")
    assert len(URLField.objects.all()) == 1

    model = table.get_model(attribute_names=True)

    valid_urls = [
        "baserow.io",
        "ftp://baserow.io",
        "git://example.com/",
        "ws://baserow.io",
        "http://baserow.io",
        "https://baserow.io",
        "https://www.baserow.io",
        "HTTP://BASEROW.IO",
        "https://test.nl/test",
        "https://test.nl/test",
        "http://localhost",
        "//localhost",
        "https://test.nl/test?with=a-query&that=has-more",
        "https://test.nl/test",
        "http://-.~_!$&'()*+,;=%40:80%2f@example.com",
        "http://उदाहरण.परीक्षा",
        "http://foo.com/(something)?after=parens",
        "http://142.42.1.1/",
        "http://userid:password@example.com:65535/",
        "http://su--b.valid-----hyphens.com/",
        "//baserow.io/test",
        "127.0.0.1",
        "https://test.nl#test",
        "http://baserow.io/hrscywv4p/image/upload/c_fill,g_faces:center,"
        "h_128,w_128/yflwk7vffgwyyenftkr7.png",
        "https://gitlab.com/bramw/baserow/-/issues?row=nice/route",
        "https://web.archive.org/web/20210313191012/https://baserow.io/",
        "mailto:bram@baserow.io?test=test",
    ]
    invalid_urls = [
        "test",
        "test.",
        "localhost",
        "\nwww.test.nl",
        "www\n.test.nl",
        "www .test.nl",
        " www.test.nl",
    ]

    for invalid_url in invalid_urls:
        with pytest.raises(ValidationError):
            row_handler.create_row(
                user=user, table=table, values={"url": invalid_url}, model=model
            )

    for url in valid_urls:
        row_handler.create_row(
            user=user,
            table=table,
            values={"url": url, "name": url},
            model=model,
        )
    for bad_url in invalid_urls:
        row_handler.create_row(
            user=user,
            table=table,
            values={"url": "", "name": bad_url},
            model=model,
        )

    # Convert the text field to a url field so we can check how the conversion of
    # values went.
    field_handler.update_field(user=user, field=field, new_type_name="url")
    rows = model.objects.all()
    i = 0
    for url in valid_urls:
        assert rows[i].url == url
        assert rows[i].name == url
        i += 1

    for _ in invalid_urls:
        assert rows[i].url == ""
        assert rows[i].name == ""
        i += 1


@pytest.mark.django_db
def test_valid_email(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_database_table(user=user, database=table.database)
    field = data_fixture.create_text_field(table=table, order=1, name="name")
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_handler.create_field(user=user, table=table, type_name="email", name="email")

    model = table.get_model(attribute_names=True)

    invalid_emails = [
        "test@" + "a" * 246 + ".com",
        "@a",
        "a@",
        "not-an-email",
        "bram.test.nl",
        "invalid_email",
        "invalid@invalid@com",
        "\nhello@gmail.com",
        "asdds asdd@gmail.com",
    ]

    for invalid_email in invalid_emails:
        with pytest.raises(ValidationError):
            row_handler.create_row(
                user=user, table=table, values={"email": invalid_email}, model=model
            )

    valid_emails = [
        "test@" + "a" * 245 + ".com",
        "a@a",
        "用户@例子.广告",
        "अजय@डाटा.भारत",
        "квіточка@пошта.укр",
        "χρήστης@παράδειγμα.ελ",
        "Dörte@Sörensen.example.com",
        "коля@пример.рф",
        "bram@localhost",
        "bram@localhost.nl",
        "first_part_underscores_ok@hyphens-ok.com",
        "wierd@[1.1.1.1]",
        "bram.test.test@sub.domain.nl",
        "BRAM.test.test@sub.DOMAIN.nl",
    ]
    for email in valid_emails:
        row_handler.create_row(
            user=user,
            table=table,
            values={"email": email, "name": email},
            model=model,
        )
    for bad_email in invalid_emails:
        row_handler.create_row(
            user=user,
            table=table,
            values={"email": "", "name": bad_email},
            model=model,
        )

    # Convert the text field to a email field so we can check how the conversion of
    # values went.
    field_handler.update_field(user=user, field=field, new_type_name="email")
    rows = model.objects.all()
    i = 0
    for email in valid_emails:
        assert rows[i].email == email
        assert rows[i].name == email
        i += 1

    for _ in invalid_emails:
        assert rows[i].email == ""
        assert rows[i].name == ""
        i += 1


@pytest.mark.django_db
def test_email_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_database_table(user=user, database=table.database)
    field = data_fixture.create_text_field(table=table, order=1, name="name")

    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_2 = field_handler.create_field(
        user=user, table=table, type_name="email", name="email"
    )
    number = field_handler.create_field(
        user=user, table=table, type_name="number", name="number"
    )

    assert len(EmailField.objects.all()) == 1
    model = table.get_model(attribute_names=True)

    row_handler.create_row(
        user=user,
        table=table,
        values={
            "name": "a.very.STRANGE@email.address.coM",
            "email": "test@test.nl",
            "number": 5,
        },
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={"name": "someuser", "email": "some@user.com", "number": 10},
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={"name": "http://www.baserow.io", "email": "bram@test.nl"},
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={"name": "NOT AN EMAIL", "email": "something@example.com"},
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={"name": "testing@nowhere.org", "email": ""},
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={
            "email": None,
        },
        model=model,
    )

    # Convert the text field to a url field so we can check how the conversion of
    # values went.
    field_handler.update_field(user=user, field=field, new_type_name="email")
    field_handler.update_field(user=user, field=number, new_type_name="email")

    model = table.get_model(attribute_names=True)
    rows = model.objects.all()

    assert rows[0].name == "a.very.STRANGE@email.address.coM"
    assert rows[0].email == "test@test.nl"
    assert rows[0].number == ""

    assert rows[1].name == ""
    assert rows[1].email == "some@user.com"
    assert rows[1].number == ""

    assert rows[2].name == ""
    assert rows[2].email == "bram@test.nl"
    assert rows[2].number == ""

    assert rows[3].name == ""
    assert rows[3].email == "something@example.com"
    assert rows[3].number == ""

    assert rows[4].name == "testing@nowhere.org"
    assert rows[4].email == ""
    assert rows[4].number == ""

    assert rows[5].name == ""
    assert rows[5].email == ""
    assert rows[5].number == ""

    field_handler.delete_field(user=user, field=field_2)
    assert len(EmailField.objects.all()) == 2


@pytest.mark.django_db
@override_settings(debug=True)
def test_phone_number_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_database_table(user=user, database=table.database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    text_field = field_handler.create_field(
        user=user, table=table, order=1, type_name="text", name="name"
    )
    phone_number_field = field_handler.create_field(
        user=user, table=table, type_name="phone_number", name="phonenumber"
    )
    email_field = field_handler.create_field(
        user=user, table=table, type_name="email", name="email"
    )
    number_field = data_fixture.create_number_field(
        table=table, order=1, number_negative=True, name="number"
    )

    assert len(PhoneNumberField.objects.all()) == 1
    model = table.get_model(attribute_names=True)

    with pytest.raises(ValidationError):
        row_handler.create_row(
            user=user,
            table=table,
            values={"phonenumber": "invalid phone number"},
            model=model,
        )

    with pytest.raises(ValidationError):
        row_handler.create_row(
            user=user,
            table=table,
            values={"phonenumber": "Phone: 2312321 2349432 "},
            model=model,
        )
    with pytest.raises(ValidationError):
        row_handler.create_row(
            user=user,
            table=table,
            values={
                "phonenumber": "1" * (PhoneNumberFieldType.MAX_PHONE_NUMBER_LENGTH + 1)
            },
            model=model,
        )

    max_length_phone_number = "1" * PhoneNumberFieldType.MAX_PHONE_NUMBER_LENGTH
    row_handler.create_row(
        user=user,
        table=table,
        values={
            "name": "+45(1424) 322314 324234",
            "phonenumber": max_length_phone_number,
            "number": 1234534532,
            "email": "a_valid_email_to_be_blanked_after_conversion@email.com",
        },
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={
            "name": "some text which should be blanked out after conversion",
            "phonenumber": "1234567890 NnXx,+._*()#=;/ -",
            "number": 0,
        },
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={
            "name": max_length_phone_number,
            "phonenumber": "",
            "number": -10230450,
        },
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={
            "phonenumber": None,
            "name": "1" * (PhoneNumberFieldType.MAX_PHONE_NUMBER_LENGTH + 1),
        },
        model=model,
    )
    row_handler.create_row(user=user, table=table, values={}, model=model)

    # No actual database type change occurs here as a phone number field is also a text
    # field. Instead the after_update hook is being used to clear out invalid
    # phone numbers.
    field_handler.update_field(
        user=user, field=text_field, new_type_name="phone_number"
    )

    field_handler.update_field(
        user=user, field=number_field, new_type_name="phone_number"
    )
    field_handler.update_field(
        user=user, field=email_field, new_type_name="phone_number"
    )

    model = table.get_model(attribute_names=True)
    rows = model.objects.all()

    assert rows[0].name == "+45(1424) 322314 324234"
    assert rows[0].phonenumber == max_length_phone_number
    assert rows[0].number == "1234534532"
    assert rows[0].email == ""

    assert rows[1].name == ""
    assert rows[1].phonenumber == "1234567890 NnXx,+._*()#=;/ -"
    assert rows[1].number == "0"

    assert rows[2].name == max_length_phone_number
    assert rows[2].phonenumber == ""
    assert rows[2].number == "-10230450"

    assert rows[3].name == ""
    assert rows[3].phonenumber == ""
    assert rows[3].number == ""

    field_handler.delete_field(user=user, field=phone_number_field)
    assert len(PhoneNumberField.objects.all()) == 3


@pytest.mark.django_db
def test_human_readable_values(data_fixture):
    table, user, row, blank_row = setup_interesting_test_table(data_fixture)
    model = table.get_model()
    results = {}
    blank_results = {}
    for field in model._field_objects.values():
        value = field["type"].get_human_readable_value(
            getattr(row, field["name"]), field
        )
        results[field["field"].name] = value
        blank_value = field["type"].get_human_readable_value(
            getattr(blank_row, field["name"]), field
        )
        blank_results[field["field"].name] = blank_value

    assert blank_results == {
        "boolean": "False",
        "date_eu": "",
        "date_us": "",
        "datetime_eu": "",
        "datetime_us": "",
        "decimal_link_row": "",
        "email": "",
        "file": "",
        "file_link_row": "",
        "link_row": "",
        "long_text": "",
        "negative_decimal": "",
        "negative_int": "",
        "phone_number": "",
        "positive_decimal": "",
        "positive_int": "",
        "single_select": "",
        "text": "",
        "url": "",
    }
    assert results == {
        "boolean": "True",
        "date_eu": "01/02/2020",
        "date_us": "02/01/2020",
        "datetime_eu": "01/02/2020 01:23",
        "datetime_us": "02/01/2020 01:23",
        "decimal_link_row": "1.234, -123.456, unnamed row 3",
        "email": "test@example.com",
        "file": "a.txt, b.txt",
        "file_link_row": "name.txt, unnamed row 2",
        "link_row": "linked_row_1, linked_row_2, unnamed row 3",
        "long_text": "long_text",
        "negative_decimal": "-1.2",
        "negative_int": "-1",
        "phone_number": "+4412345678",
        "positive_decimal": "1.2",
        "positive_int": "1",
        "single_select": "A",
        "text": "text",
        "url": "https://www.google.com",
    }

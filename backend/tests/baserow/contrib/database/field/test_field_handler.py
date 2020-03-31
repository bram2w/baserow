import pytest

from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import (
    Field, TextField, NumberField, BooleanField
)
from baserow.contrib.database.fields.exceptions import (
    FieldTypeDoesNotExist, PrimaryFieldAlreadyExists, CannotDeletePrimaryField,
    CannotChangeFieldType
)


@pytest.mark.django_db
def test_create_field(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    handler = FieldHandler()
    handler.create_field(user=user, table=table, type_name='text',
                         name='Test text field', text_default='Some default')

    assert Field.objects.all().count() == 1
    assert TextField.objects.all().count() == 1

    text_field = TextField.objects.all().first()
    assert text_field.name == 'Test text field'
    assert text_field.order == 1
    assert text_field.table == table
    assert text_field.text_default == 'Some default'
    assert not text_field.primary

    table_model = table.get_model()
    field_name = f'field_{text_field.id}'
    assert field_name in [field.name for field in table_model._meta.get_fields()]

    instance = table_model.objects.create(**{field_name: 'Test 1'})
    assert getattr(instance, field_name) == 'Test 1'

    instance_2 = table_model.objects.create()
    assert getattr(instance_2, field_name) == 'Some default'

    with pytest.raises(ValueError):
        handler.create_field(user=user, table=table, type_name='number',
                             name='Test number field', number_type='NOT_EXISTING')

    with pytest.raises(ValueError):
        handler.create_field(user=user, table=table, type_name='number',
                             name='Test number field', number_type='DECIMAL',
                             number_decimal_places=9999)

    handler.create_field(user=user, table=table, type_name='number',
                         name='Test number field', number_type='INTEGER',
                         number_decimal_places=2, number_negative=True)

    number_field = NumberField.objects.all().first()
    assert number_field.name == 'Test number field'
    assert number_field.order == 2
    assert number_field.table == table
    assert number_field.number_type == 'INTEGER'
    assert number_field.number_decimal_places == 2
    assert number_field.number_negative

    handler.create_field(user=user, table=table, type_name='boolean',
                         name='Test boolean field',
                         random_other_field='WILL_BE_IGNORED')

    boolean_field = BooleanField.objects.all().first()
    assert boolean_field.name == 'Test boolean field'
    assert boolean_field.order == 3
    assert boolean_field.table == table

    assert Field.objects.all().count() == 3
    assert TextField.objects.all().count() == 1
    assert NumberField.objects.all().count() == 1
    assert BooleanField.objects.all().count() == 1

    with pytest.raises(UserNotInGroupError):
        handler.create_field(user=user_2, table=table, type_name='text')

    with pytest.raises(FieldTypeDoesNotExist):
        handler.create_field(user=user, table=table, type_name='UNKNOWN')


@pytest.mark.django_db
def test_create_primary_field(data_fixture):
    user = data_fixture.create_user()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table_1, primary=True)

    with pytest.raises(PrimaryFieldAlreadyExists):
        handler = FieldHandler()
        handler.create_field(user=user, table=table_1, type_name='text', primary=True)

    handler = FieldHandler()
    field = handler.create_field(user=user, table=table_2, type_name='text',
                                 primary=True)

    assert field.primary

    with pytest.raises(PrimaryFieldAlreadyExists):
        handler.create_field(user=user, table=table_2, type_name='text', primary=True)

    # Should be able to create a regular field when there is already a primary field.
    handler.create_field(user=user, table=table_2, type_name='text', primary=False)


@pytest.mark.django_db
def test_update_field(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table, order=0)
    text_field_2 = data_fixture.create_text_field(table=table, order=1)

    handler = FieldHandler()

    with pytest.raises(UserNotInGroupError):
        handler.update_field(user=user_2, field=text_field_2)

    with pytest.raises(ValueError):
        handler.update_field(user=user, field=object())

    with pytest.raises(FieldTypeDoesNotExist):
        handler.update_field(user=user, field=text_field_2,
                             new_type_name='NOT_EXISTING')

    text_field_2 = handler.update_field(user=user, field=text_field_2, name='Test 1',
                                        text_default='Test 2')

    text_field_2.refresh_from_db()
    assert text_field_2.name == 'Test 1'
    assert text_field_2.text_default == 'Test 2'

    table_model = table.get_model()
    field_name = f'field_{text_field_2.id}'
    instance = table_model.objects.create(**{field_name: 'Test'})

    with pytest.raises(CannotChangeFieldType):
        handler.update_field(user=user, field=text_field_2, new_type_name='number',
                             number_type='DECIMAL')

    setattr(instance, field_name, '1')
    instance.save()

    number_field_2 = handler.update_field(user=user, field=text_field_2,
                                          new_type_name='number', number_type='DECIMAL')

    table_model = table.get_model()
    with pytest.raises(ValidationError):
        with transaction.atomic():
            table_model.objects.create(**{field_name: 'Test 1'})

    instance = table_model.objects.create(**{field_name: 2})
    assert getattr(instance, field_name) == 2

    assert Field.objects.all().count() == 2
    assert TextField.objects.all().count() == 1
    assert NumberField.objects.all().count() == 1
    assert BooleanField.objects.all().count() == 0

    handler.update_field(user=user, field=number_field_2, new_type_name='number',
                         number_type='DECIMAL', number_decimal_places=2,
                         number_negative=True)

    assert Field.objects.all().count() == 2
    assert TextField.objects.all().count() == 1
    assert NumberField.objects.all().count() == 1
    assert BooleanField.objects.all().count() == 0

    number_field = NumberField.objects.all().first()
    content_type = ContentType.objects.get_for_model(NumberField)
    assert number_field.name == 'Test 1'
    assert number_field.number_type == 'DECIMAL'
    assert number_field.number_decimal_places == 2
    assert number_field.number_negative
    assert number_field.order == 1
    assert number_field.content_type == content_type

    handler.update_field(user=user, field=number_field, new_type_name='text',
                         name='Test 2')

    assert Field.objects.all().count() == 2
    assert TextField.objects.all().count() == 2
    assert NumberField.objects.all().count() == 0
    assert BooleanField.objects.all().count() == 0

    text_field = TextField.objects.all()[1:].first()
    content_type = ContentType.objects.get_for_model(TextField)
    assert text_field.name == 'Test 2'
    assert text_field.order == 1
    assert text_field.content_type == content_type

    text_field = handler.update_field(user=user, field=text_field, name='Test 3')
    assert text_field.name == 'Test 3'

    number_field = handler.update_field(
        user=user, field=text_field, new_type_name='number', number_type='DECIMAL',
        number_decimal_places=2, number_negative=True
    )

    with pytest.raises(CannotChangeFieldType):
        handler.update_field(user=user, field=number_field, new_type_name='boolean')


@pytest.mark.django_db
def test_delete_field(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)

    handler = FieldHandler()

    with pytest.raises(UserNotInGroupError):
        handler.delete_field(user=user_2, field=text_field)

    with pytest.raises(ValueError):
        handler.delete_field(user=user_2, field=object())

    assert Field.objects.all().count() == 1
    assert TextField.objects.all().count() == 1
    handler.delete_field(user=user, field=text_field)
    assert Field.objects.all().count() == 0
    assert TextField.objects.all().count() == 0

    table_model = table.get_model()
    field_name = f'field_{text_field.id}'
    assert field_name not in [field.name for field in table_model._meta.get_fields()]

    primary = data_fixture.create_text_field(table=table, primary=True)
    with pytest.raises(CannotDeletePrimaryField):
        handler.delete_field(user=user, field=primary)

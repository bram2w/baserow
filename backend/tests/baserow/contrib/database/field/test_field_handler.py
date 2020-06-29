import pytest
from decimal import Decimal

from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import (
    Field, TextField, NumberField, BooleanField
)
from baserow.contrib.database.fields.exceptions import (
    FieldTypeDoesNotExist, PrimaryFieldAlreadyExists, CannotDeletePrimaryField,
    FieldDoesNotExist
)


@pytest.mark.django_db
def test_get_field(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    text = data_fixture.create_text_field(user=user)

    handler = FieldHandler()

    with pytest.raises(FieldDoesNotExist):
        handler.get_field(user=user, field_id=99999)

    with pytest.raises(UserNotInGroupError):
        handler.get_field(user=user_2, field_id=text.id)

    field = handler.get_field(user=user, field_id=text.id)

    assert text.id == field.id
    assert text.name == field.name
    assert isinstance(field, Field)

    field = handler.get_field(user=user, field_id=text.id, field_model=TextField)

    assert text.id == field.id
    assert text.name == field.name
    assert isinstance(field, TextField)

    # If the error is raised we know for sure that the query has resolved.
    with pytest.raises(AttributeError):
        handler.get_field(
            user=user, field_id=text.id,
            base_queryset=Field.objects.prefetch_related('UNKNOWN')
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
    """
    @TODO somehow trigger the CannotChangeFieldType and test if it is raised.
    """

    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table, order=0)
    field = data_fixture.create_text_field(table=table, order=1)

    handler = FieldHandler()

    with pytest.raises(UserNotInGroupError):
        handler.update_field(user=user_2, field=field)

    with pytest.raises(ValueError):
        handler.update_field(user=user, field=object())

    with pytest.raises(FieldTypeDoesNotExist):
        handler.update_field(user=user, field=field, new_type_name='NOT_EXISTING')

    # Change some values of the text field and test if they have been changed.
    field = handler.update_field(user=user, field=field, name='Text field',
                                 text_default='Default value')

    assert field.name == 'Text field'
    assert field.text_default == 'Default value'
    assert isinstance(field, TextField)

    # Insert some rows to the table which should be converted later.
    model = table.get_model()
    model.objects.create(**{f'field_{field.id}': 'Text value'})
    model.objects.create(**{f'field_{field.id}': '100.22'})
    model.objects.create(**{f'field_{field.id}': '10'})

    # Change the field type to a number and test if the values have been changed.
    field = handler.update_field(user=user, field=field, new_type_name='number',
                                 name='Number field', number_type='INTEGER',
                                 number_negative=False)

    assert field.name == 'Number field'
    assert field.number_type == 'INTEGER'
    assert field.number_negative == False
    assert not hasattr(field, 'text_default')

    model = table.get_model()
    rows = model.objects.all()
    assert getattr(rows[0], f'field_{field.id}') == None
    assert getattr(rows[1], f'field_{field.id}') == 100
    assert getattr(rows[2], f'field_{field.id}') == 10

    # Change the field type to a decimal and test if the values have been changed.
    field = handler.update_field(user=user, field=field, new_type_name='number',
                                 name='Price field', number_type='DECIMAL',
                                 number_decimal_places=2, number_negative=True)

    assert field.name == 'Price field'
    assert field.number_type == 'DECIMAL'
    assert field.number_decimal_places == 2
    assert field.number_negative == True

    model = table.get_model()
    rows = model.objects.all()
    assert getattr(rows[0], f'field_{field.id}') == None
    assert getattr(rows[1], f'field_{field.id}') == Decimal('100.00')
    assert getattr(rows[2], f'field_{field.id}') == Decimal('10.00')

    # Change the field type to a boolean and test if the values have been changed.
    field = handler.update_field(user=user, field=field, new_type_name='boolean',
                                 name='Active')

    field.refresh_from_db()
    assert field.name == 'Active'
    assert not hasattr(field, 'number_type')
    assert not hasattr(field, 'number_decimal_places')
    assert not hasattr(field, 'number_negative')

    model = table.get_model()
    rows = model.objects.all()
    assert getattr(rows[0], f'field_{field.id}') == False
    assert getattr(rows[1], f'field_{field.id}') == False
    assert getattr(rows[2], f'field_{field.id}') == False


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

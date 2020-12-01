import pytest

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.rows.exceptions import RowDoesNotExist


def test_get_field_ids_from_dict():
    handler = RowHandler()
    assert handler.extract_field_ids_from_dict({
        1: 'Included',
        'field_2': 'Included',
        '3': 'Included',
        'abc': 'Not included',
        'fieldd_3': 'Not included'
    }) == [1, 2, 3]


@pytest.mark.django_db
def test_extract_manytomany_values(data_fixture):
    row_handler = RowHandler()

    class TemporaryModel1(models.Model):
        class Meta:
            app_label = 'test'

    class TemporaryModel2(models.Model):
        field_1 = models.CharField()
        field_2 = models.ManyToManyField(TemporaryModel1)

        class Meta:
            app_label = 'test'

    values = {
        'field_1': 'Value 1',
        'field_2': ['Value 2']
    }

    values, manytomany_values = row_handler.extract_manytomany_values(
        values, TemporaryModel2
    )

    assert len(values.keys()) == 1
    assert 'field_1' in values
    assert len(manytomany_values.keys()) == 1
    assert 'field_2' in manytomany_values


@pytest.mark.django_db
def test_create_row(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(name='Car', user=user)
    name_field = data_fixture.create_text_field(
        table=table, name='Name', text_default='Test'
    )
    speed_field = data_fixture.create_number_field(
        table=table, name='Max speed', number_negative=True
    )
    price_field = data_fixture.create_number_field(
        table=table, name='Price', number_type='DECIMAL', number_decimal_places=2,
        number_negative=False
    )

    handler = RowHandler()

    with pytest.raises(UserNotInGroupError):
        handler.create_row(user=user_2, table=table)

    row = handler.create_row(user=user, table=table, values={
        name_field.id: 'Tesla',
        speed_field.id: 240,
        f'field_{price_field.id}': 59999.99,
        9999: 'Must not be added'
    })
    assert getattr(row, f'field_{name_field.id}') == 'Tesla'
    assert getattr(row, f'field_{speed_field.id}') == 240
    assert getattr(row, f'field_{price_field.id}') == 59999.99
    assert not getattr(row, f'field_9999', None)
    row.refresh_from_db()
    assert getattr(row, f'field_{name_field.id}') == 'Tesla'
    assert getattr(row, f'field_{speed_field.id}') == 240
    assert getattr(row, f'field_{price_field.id}') == Decimal('59999.99')
    assert not getattr(row, f'field_9999', None)

    row = handler.create_row(user=user, table=table)
    assert getattr(row, f'field_{name_field.id}') == 'Test'
    assert not getattr(row, f'field_{speed_field.id}')
    assert not getattr(row, f'field_{price_field.id}')

    with pytest.raises(ValidationError):
        handler.create_row(user=user, table=table, values={
            price_field.id: -10.22
        })

    model = table.get_model()
    assert model.objects.all().count() == 2


@pytest.mark.django_db
def test_get_row(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(name='Car', user=user)
    name_field = data_fixture.create_text_field(
        table=table, name='Name', text_default='Test'
    )
    speed_field = data_fixture.create_number_field(
        table=table, name='Max speed', number_negative=True
    )
    price_field = data_fixture.create_number_field(
        table=table, name='Price', number_type='DECIMAL', number_decimal_places=2,
        number_negative=False
    )

    handler = RowHandler()
    row = handler.create_row(user=user, table=table, values={
        f'field_{name_field.id}': 'Tesla',
        f'field_{speed_field.id}': 240,
        f'field_{price_field.id}': Decimal('59999.99')
    })

    with pytest.raises(UserNotInGroupError):
        handler.get_row(user=user_2, table=table, row_id=row.id)

    with pytest.raises(RowDoesNotExist):
        handler.get_row(user=user, table=table, row_id=99999)

    row_tmp = handler.get_row(user=user, table=table, row_id=row.id)

    assert row_tmp.id == row.id
    assert getattr(row_tmp, f'field_{name_field.id}') == 'Tesla'
    assert getattr(row_tmp, f'field_{speed_field.id}') == 240
    assert getattr(row_tmp, f'field_{price_field.id}') == Decimal('59999.99')


@pytest.mark.django_db
def test_update_row(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(name='Car', user=user)
    name_field = data_fixture.create_text_field(
        table=table, name='Name', text_default='Test'
    )
    speed_field = data_fixture.create_number_field(
        table=table, name='Max speed', number_negative=True
    )
    price_field = data_fixture.create_number_field(
        table=table, name='Price', number_type='DECIMAL', number_decimal_places=2,
        number_negative=False
    )

    handler = RowHandler()
    row = handler.create_row(user=user, table=table)

    with pytest.raises(UserNotInGroupError):
        handler.update_row(user=user_2, table=table, row_id=row.id, values={})

    with pytest.raises(RowDoesNotExist):
        handler.update_row(user=user, table=table, row_id=99999, values={})

    with pytest.raises(ValidationError):
        handler.update_row(user=user, table=table, row_id=row.id, values={
            price_field.id: -10.99
        })

    handler.update_row(user=user, table=table, row_id=row.id, values={
        name_field.id: 'Tesla',
        speed_field.id: 240,
        f'field_{price_field.id}': 59999.99
    })
    row.refresh_from_db()

    assert getattr(row, f'field_{name_field.id}') == 'Tesla'
    assert getattr(row, f'field_{speed_field.id}') == 240
    assert getattr(row, f'field_{price_field.id}') == Decimal('59999.99')


@pytest.mark.django_db
def test_delete_row(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(name='Car', user=user)
    data_fixture.create_text_field(table=table, name='Name', text_default='Test')

    handler = RowHandler()
    model = table.get_model()
    row = handler.create_row(user=user, table=table)
    handler.create_row(user=user, table=table)

    with pytest.raises(UserNotInGroupError):
        handler.delete_row(user=user_2, table=table, row_id=row.id)

    with pytest.raises(RowDoesNotExist):
        handler.delete_row(user=user, table=table, row_id=99999)

    handler.delete_row(user=user, table=table, row_id=row.id)
    assert model.objects.all().count() == 1

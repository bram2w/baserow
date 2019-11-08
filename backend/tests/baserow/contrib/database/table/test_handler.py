import pytest

from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.table.handler import TableHandler


@pytest.mark.django_db
def test_create_database_table(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)

    handler = TableHandler()
    handler.create_table(user=user, database=database, name='Test table')

    assert Table.objects.all().count() == 1

    table = Table.objects.all().first()
    assert table.name == 'Test table'
    assert table.order == 1
    assert table.database == database

    with pytest.raises(UserNotInGroupError):
        handler.create_table(user=user_2, database=database, name='')


@pytest.mark.django_db
def test_update_database_table(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    handler = TableHandler()

    with pytest.raises(UserNotInGroupError):
        handler.update_table(user=user_2, table=table, name='Test 1')

    handler.update_table(user=user, table=table, name='Test 1')

    table.refresh_from_db()

    assert table.name == 'Test 1'

@pytest.mark.django_db
def test_delete_database_application(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    handler = TableHandler()

    with pytest.raises(UserNotInGroupError):
        handler.delete_table(user=user_2, table=table)

    assert Table.objects.all().count() == 1
    handler.delete_table(user=user, table=table)
    assert Table.objects.all().count() == 0

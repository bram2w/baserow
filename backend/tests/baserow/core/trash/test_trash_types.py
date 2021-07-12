import pytest
from django.db import connection

from baserow.contrib.database.models import Database
from baserow.contrib.database.table.models import Table
from baserow.core.models import Group, GroupUser
from baserow.core.trash.handler import TrashHandler
from baserow.core.trash.trash_types import GroupTrashableItemType


@pytest.mark.django_db
def test_perm_delete_group(data_fixture):
    user = data_fixture.create_user()
    group_1 = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group_1)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_group(user=user)
    user_2 = data_fixture.create_user()
    group_3 = data_fixture.create_group(user=user_2)

    handler = GroupTrashableItemType()
    handler.permanently_delete_item(group_1)

    assert Database.objects.all().count() == 0
    assert Table.objects.all().count() == 0
    assert f"database_table_{table.id}" not in connection.introspection.table_names()
    assert Group.objects.all().count() == 2
    assert GroupUser.objects.all().count() == 2

    handler.permanently_delete_item(group_3)

    assert Group.objects.all().count() == 1
    assert GroupUser.objects.all().count() == 1


@pytest.mark.django_db
def test_perm_delete_application(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    handler = TrashHandler()

    handler.permanently_delete(database)

    assert Database.objects.all().count() == 0
    assert Table.objects.all().count() == 0
    assert f"database_table_{table.id}" not in connection.introspection.table_names()

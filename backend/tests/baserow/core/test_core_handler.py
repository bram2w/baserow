import pytest
from unittest.mock import patch

from django.db import connection

from baserow.core.handler import CoreHandler
from baserow.core.models import Group, GroupUser, Application
from baserow.core.exceptions import (
    UserNotInGroupError, ApplicationTypeDoesNotExist, GroupDoesNotExist,
    ApplicationDoesNotExist
)
from baserow.contrib.database.models import Database, Table


@pytest.mark.django_db
def test_get_group(data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group_1 = data_fixture.create_group(user=user_1)

    handler = CoreHandler()

    with pytest.raises(GroupDoesNotExist):
        handler.get_group(user=user_1, group_id=0)

    with pytest.raises(UserNotInGroupError):
        handler.get_group(user=user_2, group_id=group_1.id)

    group_1_copy = handler.get_group(user=user_1, group_id=group_1.id)
    assert group_1_copy.id == group_1.id

    # If the error is raised we know for sure that the query has resolved.
    with pytest.raises(AttributeError):
        handler.get_group(
            user=user_1, group_id=group_1.id,
            base_queryset=Group.objects.prefetch_related('UNKNOWN')
        )


@pytest.mark.django_db
def test_get_group_user(data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group_1 = data_fixture.create_group(user=user_1)

    handler = CoreHandler()

    with pytest.raises(GroupDoesNotExist):
        handler.get_group_user(user=user_1, group_id=0)

    with pytest.raises(UserNotInGroupError):
        handler.get_group_user(user=user_2, group_id=group_1.id)

    group_user_1_copy = handler.get_group_user(user=user_1, group_id=group_1.id)
    assert group_user_1_copy.group_id == group_1.id

    # If the error is raised we know for sure that the query has resolved.
    with pytest.raises(AttributeError):
        handler.get_group_user(
            user=user_1, group_id=group_1.id,
            base_queryset=GroupUser.objects.prefetch_related('UNKNOWN')
        )


@pytest.mark.django_db
@patch('baserow.core.signals.group_created.send')
def test_create_group(send_mock, data_fixture):
    user = data_fixture.create_user()

    handler = CoreHandler()
    group_user = handler.create_group(user=user, name='Test group')

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['group'].id == group_user.group.id
    assert send_mock.call_args[1]['user'].id == user.id

    group = Group.objects.all().first()
    user_group = GroupUser.objects.all().first()

    assert group.name == 'Test group'
    assert user_group.user == user
    assert user_group.group == group
    assert user_group.order == 1

    handler.create_group(user=user, name='Test group 2')

    assert Group.objects.all().count() == 2
    assert GroupUser.objects.all().count() == 2


@pytest.mark.django_db
@patch('baserow.core.signals.group_updated.send')
def test_update_group(send_mock, data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user_1)

    handler = CoreHandler()
    handler.update_group(user=user_1, group=group, name='New name')

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['group'].id == group.id
    assert send_mock.call_args[1]['user'].id == user_1.id

    group.refresh_from_db()

    assert group.name == 'New name'

    with pytest.raises(UserNotInGroupError):
        handler.update_group(user=user_2, group=group, name='New name')

    with pytest.raises(ValueError):
        handler.update_group(user=user_2, group=object(), name='New name')


@pytest.mark.django_db
@patch('baserow.core.signals.group_deleted.send')
def test_delete_group(send_mock, data_fixture):
    user = data_fixture.create_user()
    group_1 = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group_1)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_group(user=user)
    user_2 = data_fixture.create_user()
    group_3 = data_fixture.create_group(user=user_2)

    handler = CoreHandler()
    handler.delete_group(user, group_1)

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['group'].id == group_1.id
    assert send_mock.call_args[1]['user'].id == user.id
    assert len(send_mock.call_args[1]['group_users']) == 1
    assert send_mock.call_args[1]['group_users'][0].id == user.id

    assert Database.objects.all().count() == 0
    assert Table.objects.all().count() == 0
    assert f'database_table_{table.id}' not in connection.introspection.table_names()
    assert Group.objects.all().count() == 2
    assert GroupUser.objects.all().count() == 2

    with pytest.raises(UserNotInGroupError):
        handler.delete_group(user, group_3)

    handler.delete_group(user_2, group_3)

    assert Group.objects.all().count() == 1
    assert GroupUser.objects.all().count() == 1

    with pytest.raises(ValueError):
        handler.delete_group(user=user_2, group=object())


@pytest.mark.django_db
def test_order_groups(data_fixture):
    user = data_fixture.create_user()
    ug_1 = data_fixture.create_user_group(user=user, order=1)
    ug_2 = data_fixture.create_user_group(user=user, order=2)
    ug_3 = data_fixture.create_user_group(user=user, order=3)

    assert [1, 2, 3] == [ug_1.order, ug_2.order, ug_3.order]

    handler = CoreHandler()
    handler.order_groups(user, [ug_3.group.id, ug_2.group.id, ug_1.group.id])

    ug_1.refresh_from_db()
    ug_2.refresh_from_db()
    ug_3.refresh_from_db()

    assert [1, 2, 3] == [ug_3.order, ug_2.order, ug_1.order]

    handler.order_groups(user, [ug_2.group.id, ug_1.group.id, ug_3.group.id])

    ug_1.refresh_from_db()
    ug_2.refresh_from_db()
    ug_3.refresh_from_db()

    assert [1, 2, 3] == [ug_2.order, ug_1.order, ug_3.order]


@pytest.mark.django_db
def test_get_application(data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    application_1 = data_fixture.create_database_application(user=user_1)

    handler = CoreHandler()

    with pytest.raises(ApplicationDoesNotExist):
        handler.get_application(user=user_1, application_id=0)

    with pytest.raises(UserNotInGroupError):
        handler.get_application(user=user_2, application_id=application_1.id)

    application_1_copy = handler.get_application(
        user=user_1, application_id=application_1.id
    )
    assert application_1_copy.id == application_1.id
    assert isinstance(application_1_copy, Application)

    database_1_copy = handler.get_application(
        user=user_1, application_id=application_1.id, base_queryset=Database.objects
    )
    assert database_1_copy.id == application_1.id
    assert isinstance(database_1_copy, Database)


@pytest.mark.django_db
@patch('baserow.core.signals.application_created.send')
def test_create_database_application(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)

    handler = CoreHandler()
    handler.create_application(user=user, group=group, type_name='database',
                               name='Test database')

    assert Application.objects.all().count() == 1
    assert Database.objects.all().count() == 1

    database = Database.objects.all().first()
    assert database.name == 'Test database'
    assert database.order == 1
    assert database.group == group

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['application'].id == database.id
    assert send_mock.call_args[1]['user'].id == user.id
    assert send_mock.call_args[1]['type_name'] == 'database'

    with pytest.raises(UserNotInGroupError):
        handler.create_application(user=user_2, group=group, type_name='database',
                                   name='')

    with pytest.raises(ApplicationTypeDoesNotExist):
        handler.create_application(user=user, group=group, type_name='UNKNOWN',
                                   name='')


@pytest.mark.django_db
@patch('baserow.core.signals.application_updated.send')
def test_update_database_application(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)

    handler = CoreHandler()

    with pytest.raises(UserNotInGroupError):
        handler.update_application(user=user_2, application=database, name='Test 1')

    with pytest.raises(ValueError):
        handler.update_application(user=user_2, application=object(), name='Test 1')

    handler.update_application(user=user, application=database, name='Test 1')

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['application'].id == database.id
    assert send_mock.call_args[1]['user'].id == user.id

    database.refresh_from_db()

    assert database.name == 'Test 1'


@pytest.mark.django_db
@patch('baserow.core.signals.application_deleted.send')
def test_delete_database_application(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    handler = CoreHandler()

    with pytest.raises(UserNotInGroupError):
        handler.delete_application(user=user_2, application=database)

    with pytest.raises(ValueError):
        handler.delete_application(user=user_2, application=object())

    handler.delete_application(user=user, application=database)

    assert Database.objects.all().count() == 0
    assert Table.objects.all().count() == 0
    assert f'database_table_{table.id}' not in connection.introspection.table_names()

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['application_id'] == database.id
    assert send_mock.call_args[1]['application'].id == database.id
    assert send_mock.call_args[1]['user'].id == user.id

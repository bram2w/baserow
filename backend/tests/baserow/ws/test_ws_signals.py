from unittest.mock import patch

import pytest

from baserow.core.handler import CoreHandler
from baserow.core.models import (
    GROUP_USER_PERMISSION_ADMIN,
    GROUP_USER_PERMISSION_MEMBER,
)
from baserow.core.trash.handler import TrashHandler


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
def test_group_created(mock_broadcast_to_group, data_fixture):
    user = data_fixture.create_user()
    group_user = CoreHandler().create_group(user=user, name="Test")

    mock_broadcast_to_group.delay.assert_called_once()
    args = mock_broadcast_to_group.delay.call_args
    assert args[0][0] == group_user.group_id
    assert args[0][1]["type"] == "group_created"
    assert args[0][1]["group"]["id"] == group_user.group_id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_users")
def test_group_restored(mock_broadcast_to_users, data_fixture):
    user = data_fixture.create_user()
    member_user = data_fixture.create_user()
    # This user should not be sent the restore signal
    data_fixture.create_user()
    group = data_fixture.create_group()
    group_user = data_fixture.create_user_group(
        user=user, group=group, permissions=GROUP_USER_PERMISSION_ADMIN
    )
    member_group_user = data_fixture.create_user_group(
        user=member_user, group=group, permissions=GROUP_USER_PERMISSION_MEMBER
    )
    database = data_fixture.create_database_application(user=user, group=group)
    TrashHandler.trash(user, group, None, group)

    TrashHandler.restore_item(user, "group", group.id)

    args = mock_broadcast_to_users.delay.call_args_list
    assert len(args) == 2
    member_call = args[1][0]
    admin_call = args[0][0]
    assert member_call[0] == [member_user.id]
    assert member_call[1]["type"] == "group_restored"
    assert member_call[1]["group"]["id"] == member_group_user.group_id
    assert member_call[1]["group"]["permissions"] == "MEMBER"
    expected_group_json = {
        "id": database.id,
        "name": database.name,
        "order": 0,
        "type": "database",
        "tables": [],
        "group": {"id": group.id, "name": group.name},
    }
    assert member_call[1]["applications"] == [expected_group_json]
    assert admin_call[0] == [user.id]
    assert admin_call[1]["type"] == "group_restored"
    assert admin_call[1]["group"]["id"] == group_user.group_id
    assert admin_call[1]["group"]["permissions"] == "ADMIN"
    assert admin_call[1]["group"]["id"] == group_user.group_id
    assert admin_call[1]["applications"] == [expected_group_json]


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
def test_group_updated(mock_broadcast_to_group, data_fixture):
    user = data_fixture.create_user()
    user.web_socket_id = "test"
    group = data_fixture.create_group(user=user)
    group = CoreHandler().update_group(user=user, group=group, name="Test")

    mock_broadcast_to_group.delay.assert_called_once()
    args = mock_broadcast_to_group.delay.call_args
    assert args[0][0] == group.id
    assert args[0][1]["type"] == "group_updated"
    assert args[0][1]["group_id"] == group.id
    assert args[0][1]["group"]["id"] == group.id
    assert args[0][2] == "test"


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_users")
def test_group_deleted(mock_broadcast_to_users, data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    group_id = group.id
    CoreHandler().delete_group(user=user, group=group)

    mock_broadcast_to_users.delay.assert_called_once()
    args = mock_broadcast_to_users.delay.call_args
    assert args[0][0] == [user.id]
    assert args[0][1]["type"] == "group_deleted"
    assert args[0][1]["group_id"] == group_id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_users")
def test_group_user_updated(mock_broadcast_to_users, data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group()
    group_user_1 = data_fixture.create_user_group(user=user_1, group=group)
    data_fixture.create_user_group(user=user_2, group=group)
    CoreHandler().update_group_user(
        user=user_2, group_user=group_user_1, permissions="MEMBER"
    )

    mock_broadcast_to_users.delay.assert_called_once()
    args = mock_broadcast_to_users.delay.call_args
    assert args[0][0] == [user_1.id]
    assert args[0][1]["type"] == "group_updated"
    assert args[0][1]["group"]["id"] == group.id
    assert args[0][1]["group"]["name"] == group.name
    assert args[0][1]["group"]["permissions"] == "MEMBER"
    assert args[0][1]["group_id"] == group.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_users")
def test_group_user_deleted(mock_broadcast_to_users, data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group()
    group_user_1 = data_fixture.create_user_group(user=user_1, group=group)
    data_fixture.create_user_group(user=user_2, group=group)
    CoreHandler().delete_group_user(user=user_2, group_user=group_user_1)

    mock_broadcast_to_users.delay.assert_called_once()
    args = mock_broadcast_to_users.delay.call_args
    assert args[0][0] == [user_1.id]
    assert args[0][1]["type"] == "group_deleted"
    assert args[0][1]["group_id"] == group.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
def test_application_created(mock_broadcast_to_group, data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = CoreHandler().create_application(
        user=user, group=group, type_name="database", name="Database"
    )

    mock_broadcast_to_group.delay.assert_called_once()
    args = mock_broadcast_to_group.delay.call_args
    assert args[0][0] == group.id
    assert args[0][1]["type"] == "application_created"
    assert args[0][1]["application"]["id"] == database.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
def test_application_updated(mock_broadcast_to_group, data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    CoreHandler().update_application(user=user, application=database, name="Database")

    mock_broadcast_to_group.delay.assert_called_once()
    args = mock_broadcast_to_group.delay.call_args
    assert args[0][0] == database.group_id
    assert args[0][1]["type"] == "application_updated"
    assert args[0][1]["application_id"] == database.id
    assert args[0][1]["application"]["id"] == database.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
def test_application_deleted(mock_broadcast_to_group, data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    database_id = database.id
    CoreHandler().delete_application(user=user, application=database)

    mock_broadcast_to_group.delay.assert_called_once()
    args = mock_broadcast_to_group.delay.call_args
    assert args[0][0] == database.group_id
    assert args[0][1]["type"] == "application_deleted"
    assert args[0][1]["application_id"] == database_id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
def test_applications_reordered(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    CoreHandler().order_applications(user=user, group=group, order=[database.id])

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == database.group_id
    assert args[0][1]["type"] == "applications_reordered"
    assert args[0][1]["group_id"] == group.id
    assert args[0][1]["order"] == [database.id]

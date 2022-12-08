from datetime import timedelta
from unittest.mock import patch

from django.db import transaction
from django.utils import timezone

import pytest

from baserow.core.handler import CoreHandler
from baserow.core.models import (
    GROUP_USER_PERMISSION_ADMIN,
    GROUP_USER_PERMISSION_MEMBER,
)
from baserow.core.trash.handler import TrashHandler
from baserow.core.user.handler import UserHandler


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_groups")
def test_user_updated_name(mock_broadcast_to_groups, data_fixture):
    user = data_fixture.create_user(first_name="Albert")
    group_user = CoreHandler().create_group(user=user, name="Test")
    group_user_2 = CoreHandler().create_group(user=user, name="Test 2")

    UserHandler().update_user(user, first_name="Jack")

    mock_broadcast_to_groups.delay.assert_called_once()
    args = mock_broadcast_to_groups.delay.call_args
    assert args[0][0] == [group_user.group.id, group_user_2.group.id]
    assert args[0][1]["type"] == "user_updated"
    assert args[0][1]["user"]["id"] == user.id
    assert args[0][1]["user"]["first_name"] == "Jack"


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_groups")
def test_schedule_user_deletion(mock_broadcast_to_groups, data_fixture):
    user = data_fixture.create_user(first_name="Albert", password="albert")
    group_user = CoreHandler().create_group(user=user, name="Test")
    group_user_2 = CoreHandler().create_group(user=user, name="Test 2")

    UserHandler().schedule_user_deletion(user)

    mock_broadcast_to_groups.delay.assert_called_once()
    args = mock_broadcast_to_groups.delay.call_args
    assert args[0][0] == [group_user.group.id, group_user_2.group.id]
    assert args[0][1]["type"] == "user_deleted"
    assert args[0][1]["user"]["id"] == user.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_groups")
def test_cancel_user_deletion(mock_broadcast_to_groups, data_fixture):
    user = data_fixture.create_user(first_name="Albert", password="albert")
    user.profile.to_be_deleted = True
    user.save()
    group_user = CoreHandler().create_group(user=user, name="Test")
    group_user_2 = CoreHandler().create_group(user=user, name="Test 2")

    UserHandler().cancel_user_deletion(user)

    mock_broadcast_to_groups.delay.assert_called_once()
    args = mock_broadcast_to_groups.delay.call_args
    assert args[0][0] == [group_user.group.id, group_user_2.group.id]
    assert args[0][1]["type"] == "user_restored"
    assert args[0][1]["user"]["id"] == user.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_groups")
def test_user_permanently_deleted(mock_broadcast_to_groups, data_fixture):
    user = data_fixture.create_user(first_name="Albert", password="albert")
    user.profile.to_be_deleted = True
    user.profile.save()
    user.last_login = timezone.now() - timedelta(weeks=100)
    user.save()
    group_user = CoreHandler().create_group(user=user, name="Test")
    group_user_2 = CoreHandler().create_group(user=user, name="Test 2")

    UserHandler().delete_expired_users(grace_delay=timedelta(days=1))

    mock_broadcast_to_groups.delay.assert_called_once()
    args = mock_broadcast_to_groups.delay.call_args
    assert args[0][0] == [group_user.group.id, group_user_2.group.id]
    assert args[0][1]["type"] == "user_permanently_deleted"
    assert args[0][1]["user_id"] == user.id


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
    with transaction.atomic():
        group = CoreHandler().get_group_for_update(group.id)
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
    with transaction.atomic():
        group = CoreHandler().get_group_for_update(group_id)
        CoreHandler().delete_group(user=user, group=group)

    mock_broadcast_to_users.delay.assert_called_once()
    args = mock_broadcast_to_users.delay.call_args
    assert args[0][0] == [user.id]
    assert args[0][1]["type"] == "group_deleted"
    assert args[0][1]["group_id"] == group_id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
def test_group_user_added(mock_broadcast_to_group, data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group()
    group_user_1 = data_fixture.create_user_group(user=user_1, group=group)
    group_invitation = data_fixture.create_group_invitation(
        email=user_2.email, permissions="MEMBER", group=group
    )

    group_user_2 = CoreHandler().accept_group_invitation(user_2, group_invitation)

    mock_broadcast_to_group.delay.assert_called_once()
    args = mock_broadcast_to_group.delay.call_args
    assert args[0][0] == group.id
    assert args[0][1]["type"] == "group_user_added"
    assert args[0][1]["id"] == group_user_2.id
    assert args[0][1]["group_id"] == group.id
    assert args[0][1]["group_user"]["user_id"] == group_user_2.user_id
    assert args[0][1]["group_user"]["permissions"] == "MEMBER"


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
def test_group_user_updated(mock_broadcast_to_group, data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group()
    group_user_1 = data_fixture.create_user_group(user=user_1, group=group)
    data_fixture.create_user_group(user=user_2, group=group)
    CoreHandler().update_group_user(
        user=user_2, group_user=group_user_1, permissions="MEMBER"
    )

    mock_broadcast_to_group.delay.assert_called_once()
    args = mock_broadcast_to_group.delay.call_args
    assert args[0][0] == group.id
    assert args[0][1]["type"] == "group_user_updated"
    assert args[0][1]["id"] == group_user_1.id
    assert args[0][1]["group_id"] == group.id
    assert args[0][1]["group_user"]["user_id"] == group_user_1.user_id
    assert args[0][1]["group_user"]["permissions"] == "MEMBER"


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
@patch("baserow.ws.signals.broadcast_to_users")
def test_group_user_deleted(
    mock_broadcast_to_users, mock_broadcast_to_group, data_fixture
):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group()
    group_user_1 = data_fixture.create_user_group(user=user_1, group=group)
    group_user_id = group_user_1.id
    data_fixture.create_user_group(user=user_2, group=group)
    CoreHandler().delete_group_user(user=user_2, group_user=group_user_1)

    mock_broadcast_to_users.delay.assert_called_once()
    args = mock_broadcast_to_users.delay.call_args
    assert args[0][0] == [user_1.id]
    assert args[0][1]["type"] == "group_user_deleted"
    assert args[0][1]["id"] == group_user_id
    assert args[0][1]["group_id"] == group.id
    assert args[0][1]["group_user"]["user_id"] == group_user_1.user_id

    mock_broadcast_to_group.delay.assert_called_once()
    args = mock_broadcast_to_group.delay.call_args
    assert args[0][0] == group.id
    assert args[0][1]["type"] == "group_user_deleted"
    assert args[0][1]["id"] == group_user_id
    assert args[0][1]["group_id"] == group.id
    assert args[0][1]["group_user"]["user_id"] == group_user_1.user_id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
@patch("baserow.ws.signals.broadcast_to_users")
def test_user_leaves_group(
    mock_broadcast_to_users, mock_broadcast_to_group, data_fixture
):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group()
    group_user_1 = data_fixture.create_user_group(user=user_1, group=group)
    group_user_id = group_user_1.id
    data_fixture.create_user_group(user=user_2, group=group)
    CoreHandler().leave_group(user_1, group)

    mock_broadcast_to_users.delay.assert_called_once()
    args = mock_broadcast_to_users.delay.call_args
    assert args[0][0] == [user_1.id]
    assert args[0][1]["type"] == "group_user_deleted"
    assert args[0][1]["id"] == group_user_id
    assert args[0][1]["group_id"] == group.id
    assert args[0][1]["group_user"]["user_id"] == group_user_1.user_id

    mock_broadcast_to_group.delay.assert_called_once()
    args = mock_broadcast_to_group.delay.call_args
    assert args[0][0] == group.id
    assert args[0][1]["type"] == "group_user_deleted"
    assert args[0][1]["id"] == group_user_id
    assert args[0][1]["group_id"] == group.id
    assert args[0][1]["group_user"]["user_id"] == group_user_1.user_id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_users")
def test_groups_reordered(mock_broadcast_to_users, data_fixture):
    user = data_fixture.create_user()
    group_1 = data_fixture.create_group(user=user)
    group_2 = data_fixture.create_group(user=user)
    group_3 = data_fixture.create_group(user=user)

    CoreHandler().order_groups(
        user=user, group_ids=[group_1.id, group_2.id, group_3.id]
    )

    mock_broadcast_to_users.delay.assert_called_once()
    args = mock_broadcast_to_users.delay.call_args
    assert args[0][0] == [user.id]
    assert args[0][1]["type"] == "groups_reordered"
    assert args[0][1]["group_ids"] == [group_1.id, group_2.id, group_3.id]


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


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
def test_duplicate_application(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)

    with transaction.atomic():
        application_clone = CoreHandler().duplicate_application(
            user=user, application=database
        )

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == group.id
    assert args[0][1]["type"] == "application_created"
    assert args[0][1]["application"]["id"] == application_clone.id

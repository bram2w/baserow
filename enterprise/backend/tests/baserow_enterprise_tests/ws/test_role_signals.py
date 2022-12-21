from django.apps import apps
from django.db import transaction

import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator

from baserow.config.asgi import application
from baserow.core.apps import sync_operations_after_migrate
from baserow_enterprise.apps import sync_default_roles_after_migrate
from baserow_enterprise.role.default_roles import NO_ROLE_LOW_PRIORITY
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role
from baserow_enterprise.teams.handler import TeamHandler
from tests.baserow.contrib.database.utils import received_message


# We have to run this every time between test executions since we are using
# `transaction=True`for some of the tests which flushes the DB and deletes the roles
@pytest.fixture(autouse=True)
def synced_roles(db):
    sync_operations_after_migrate(None, apps=apps)
    sync_default_roles_after_migrate(None, apps=apps)

    def resetRoleAssignmentHandlerCache():
        # Reset the cache at the beginning of the tests to prevent invalid cache when
        # a previous transaction has been rolled back.

        RoleAssignmentHandler._init = False

    transaction.on_commit(resetRoleAssignmentHandlerCache)

    yield

    sync_operations_after_migrate(None, apps=apps)
    sync_default_roles_after_migrate(None, apps=apps)
    transaction.on_commit(resetRoleAssignmentHandlerCache)


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise):
    pass


@pytest.fixture(autouse=True)
def use_async_event_loop_here(async_event_loop):
    pass


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_unsubscribe_subject_from_table_role_deleted(data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    builder_role = Role.objects.get(uid="BUILDER")

    # Assign an initial role to the user
    await sync_to_async(RoleAssignmentHandler().assign_role)(user, group, builder_role)

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await communicator.send_json_to({"page": "table", "table_id": table.id})
    await communicator.receive_json_from()

    # Remove role from user
    await sync_to_async(RoleAssignmentHandler().assign_role)(user, group, None)

    # Make sure the user has been un-subscribed
    assert await received_message(communicator, "page_discard") is True
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_unsubscribe_subject_from_table_role_no_role(data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    builder_role = Role.objects.get(uid="BUILDER")
    no_role_role = Role.objects.get(uid=NO_ROLE_LOW_PRIORITY)

    # Assign an initial role to the user
    await sync_to_async(RoleAssignmentHandler().assign_role)(user, group, builder_role)

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await communicator.send_json_to({"page": "table", "table_id": table.id})
    await communicator.receive_json_from()

    # Remove role from user
    await sync_to_async(RoleAssignmentHandler().assign_role)(user, group, no_role_role)

    # Make sure the user has been un-subscribed
    assert await received_message(communicator, "page_discard") is True
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_unsubscribe_subject_from_table_unrelated_user(data_fixture):
    user = data_fixture.create_user()
    unrelated_user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user, members=[unrelated_user])
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    builder_role = Role.objects.get(uid="BUILDER")

    # Assign an initial role to the user
    await sync_to_async(RoleAssignmentHandler().assign_role)(user, group, builder_role)

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await communicator.send_json_to({"page": "table", "table_id": table.id})
    await communicator.receive_json_from()

    # Remove role from user
    await sync_to_async(RoleAssignmentHandler().assign_role)(user, group, None)

    # Make sure the user has been un-subscribed
    assert await received_message(communicator, "page_discard") is False
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_unsubscribe_subject_from_table_new_role_no_access(data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(members=[user])
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await communicator.send_json_to({"page": "table", "table_id": table.id})
    await communicator.receive_json_from()

    # Deny user access to the table
    await sync_to_async(RoleAssignmentHandler().assign_role)(
        user, group, no_access_role, table
    )

    # Make sure the user has been un-subscribed
    assert await received_message(communicator, "page_discard") is True
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_unsubscribe_subject_from_table_role_updated(data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    builder_role = Role.objects.get(uid="BUILDER")
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    # Assign an initial role to the user
    await sync_to_async(RoleAssignmentHandler().assign_role)(user, group, builder_role)

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await communicator.send_json_to({"page": "table", "table_id": table.id})
    await communicator.receive_json_from()

    # Remove role from user
    await sync_to_async(RoleAssignmentHandler().assign_role)(
        user, group, no_access_role
    )

    # Make sure the user has been un-subscribed
    assert await received_message(communicator, "page_discard") is True
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_unsubscribe_subject_from_table_should_still_have_access(data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    builder_role = Role.objects.get(uid="BUILDER")

    # Assign an initial role to the user
    await sync_to_async(RoleAssignmentHandler().assign_role)(
        user, group, builder_role, table
    )

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await communicator.send_json_to({"page": "table", "table_id": table.id})
    await communicator.receive_json_from()

    # Remove role from user, in this case the user still has their group level
    # role and is therefore still able to see the table
    await sync_to_async(RoleAssignmentHandler().assign_role)(user, group, None, table)

    # Make sure the user is still subscribed
    assert await received_message(communicator, "page_discard") is False
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_unsubscribe_subject_from_table_teams(
    data_fixture, enterprise_data_fixture
):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(custom_permissions=[(user, "NO_ACCESS")])
    team = enterprise_data_fixture.create_team(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    builder_role = Role.objects.get(uid="BUILDER")

    # Add user to team
    enterprise_data_fixture.create_subject(team, user)

    # Set initial role for team
    await sync_to_async(RoleAssignmentHandler().assign_role)(
        team, group, builder_role, table
    )

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await communicator.send_json_to({"page": "table", "table_id": table.id})
    await communicator.receive_json_from()

    await sync_to_async(RoleAssignmentHandler().assign_role)(team, group, None, table)

    assert await received_message(communicator, "page_discard") is True
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_unsubscribe_subject_from_table_teams_when_team_trashed(
    data_fixture, enterprise_data_fixture
):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(custom_permissions=[(user, "NO_ACCESS")])
    team = enterprise_data_fixture.create_team(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    builder_role = Role.objects.get(uid="BUILDER")

    # Add user to team
    enterprise_data_fixture.create_subject(team, user)

    # Set initial role for team
    await sync_to_async(RoleAssignmentHandler().assign_role)(
        team, group, builder_role, table
    )

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await communicator.send_json_to({"page": "table", "table_id": table.id})
    await communicator.receive_json_from()

    await sync_to_async(TeamHandler().delete_team)(user, team)

    assert await received_message(communicator, "page_discard") is True
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_unsubscribe_subject_from_table_teams_still_connected(
    data_fixture, enterprise_data_fixture
):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    team = enterprise_data_fixture.create_team(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    builder_role = Role.objects.get(uid="BUILDER")

    # Add user to team
    enterprise_data_fixture.create_subject(team, user)

    # Set initial role for team
    await sync_to_async(RoleAssignmentHandler().assign_role)(
        team, group, builder_role, table
    )

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await communicator.send_json_to({"page": "table", "table_id": table.id})
    await communicator.receive_json_from()

    await sync_to_async(RoleAssignmentHandler().assign_role)(team, group, None, table)

    assert await received_message(communicator, "page_discard") is False
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_unsubscribe_subject_from_table_teams_multiple_users(
    data_fixture, enterprise_data_fixture
):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    group = data_fixture.create_group(
        custom_permissions=[(user, "NO_ACCESS"), (user_2, "NO_ACCESS")]
    )
    team = enterprise_data_fixture.create_team(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    builder_role = Role.objects.get(uid="BUILDER")

    # Add user to team
    enterprise_data_fixture.create_subject(team, user)
    enterprise_data_fixture.create_subject(team, user_2)

    # Set initial role for team
    await sync_to_async(RoleAssignmentHandler().assign_role)(
        team, group, builder_role, table
    )

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await communicator.send_json_to({"page": "table", "table_id": table.id})
    await communicator.receive_json_from()

    communicator_2 = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token_2}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator_2.connect()
    await communicator_2.receive_json_from()

    await communicator_2.send_json_to({"page": "table", "table_id": table.id})
    await communicator_2.receive_json_from()

    await sync_to_async(RoleAssignmentHandler().assign_role)(team, group, None, table)

    assert await received_message(communicator, "page_discard") is True
    assert await received_message(communicator_2, "page_discard") is True
    await communicator.disconnect()
    await communicator_2.disconnect()

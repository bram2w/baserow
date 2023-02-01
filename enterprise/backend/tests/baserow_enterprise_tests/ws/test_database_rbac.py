import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator

from baserow.api.applications.serializers import get_application_serializer
from baserow.config.asgi import application
from baserow.core.handler import CoreHandler
from baserow.core.trash.handler import TrashHandler
from baserow.core.trash.trash_types import (
    ApplicationTrashableItemType,
    GroupTrashableItemType,
)
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role
from tests.baserow.contrib.database.utils import get_message, received_message


@pytest.fixture(autouse=True)
def enable_enterprise_and_roles_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.fixture(autouse=True)
def use_async_event_loop_here(async_event_loop):
    pass


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_database_updated_message_not_leaking(data_fixture):
    user = data_fixture.create_user()
    user_excluded, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user, members=[user_excluded])
    database = data_fixture.create_database_application(group=group)
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    await sync_to_async(RoleAssignmentHandler().assign_role)(
        user_excluded, group, no_access_role, database.application_ptr
    )

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await sync_to_async(CoreHandler().update_application)(
        user=user, application=database, name="Test"
    )

    assert await received_message(communicator, "application_updated") is False
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_database_deleted_message_not_leaking(data_fixture):
    user = data_fixture.create_user()
    user_excluded, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user, members=[user_excluded])
    database = data_fixture.create_database_application(group=group)
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    await sync_to_async(RoleAssignmentHandler().assign_role)(
        user_excluded, group, no_access_role, database.application_ptr
    )

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await sync_to_async(CoreHandler().delete_application)(
        user=user, application=database
    )

    assert await received_message(communicator, "application_deleted") is False
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_database_created_message_not_leaking(data_fixture):
    user = data_fixture.create_user()
    user_excluded, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user, members=[user_excluded])
    database = data_fixture.create_database_application(group=group)
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    await sync_to_async(RoleAssignmentHandler().assign_role)(
        user_excluded, group, no_access_role, database.application_ptr
    )

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await sync_to_async(CoreHandler().delete_application)(
        user=user, application=database
    )

    await sync_to_async(TrashHandler().restore_item)(
        user, ApplicationTrashableItemType.type, database.id
    )

    assert await received_message(communicator, "application_created") is False
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_group_restored_applications_arent_leaked(data_fixture):
    user_excluded, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user_excluded)
    database = data_fixture.create_database_application(group=group)
    database_excluded = data_fixture.create_database_application(group=group)
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    await sync_to_async(RoleAssignmentHandler().assign_role)(
        user_excluded,
        group,
        role=no_access_role,
        scope=database_excluded.application_ptr,
    )

    # Establish websocket connection and subscribe to table
    communicator = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator.connect()
    await communicator.receive_json_from()

    await sync_to_async(TrashHandler.trash)(
        user_excluded, group, None, trash_item=group
    )
    await sync_to_async(TrashHandler.restore_item)(
        user_excluded, GroupTrashableItemType.type, group.id
    )

    group_restored_message = await get_message(communicator, "group_restored")
    assert group_restored_message is not None
    assert group_restored_message["applications"] == [
        get_application_serializer(database).data
    ]
    await communicator.disconnect()

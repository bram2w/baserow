import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator

from baserow.config.asgi import application
from baserow.core.handler import CoreHandler
from baserow.core.models import GroupUser
from tests.baserow.contrib.database.utils import received_message


@pytest.fixture(autouse=True)
def use_async_event_loop_here(async_event_loop):
    pass


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_unsubscribe_subject_from_table_group_user_deleted(data_fixture):
    group_owner = data_fixture.create_user()
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=group_owner, members=[user])
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

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

    # Kick user from group
    await sync_to_async(CoreHandler().delete_group_user)(
        group_owner, GroupUser.objects.get(user=user, group=group)
    )

    # Make sure the user has been un-subscribed
    assert await received_message(communicator, "page_discard") is True
    await communicator.disconnect()

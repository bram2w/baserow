import pytest

from asgiref.sync import sync_to_async

from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from baserow.config.asgi import application
from baserow.ws.tasks import (
    broadcast_to_users,
    broadcast_to_channel_group,
    broadcast_to_group,
)


@pytest.mark.run(order=4)
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_broadcast_to_users(data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()

    communicator_1 = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token_1}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator_1.connect()
    response_1 = await communicator_1.receive_json_from()
    web_socket_id_1 = response_1["web_socket_id"]

    communicator_2 = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token_2}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator_2.connect()
    response_2 = await communicator_2.receive_json_from()
    response_2["web_socket_id"]

    await sync_to_async(broadcast_to_users)([user_1.id], {"message": "test"})
    response_1 = await communicator_1.receive_json_from(0.1)
    await communicator_2.receive_nothing(0.1)
    assert response_1["message"] == "test"

    await sync_to_async(broadcast_to_users)(
        [user_1.id, user_2.id],
        {"message": "test"},
        ignore_web_socket_id=web_socket_id_1,
    )
    await communicator_1.receive_nothing(0.1)
    response_2 = await communicator_2.receive_json_from(0.1)
    assert response_2["message"] == "test"

    assert communicator_1.output_queue.qsize() == 0
    assert communicator_2.output_queue.qsize() == 0

    await communicator_1.disconnect()
    await communicator_2.disconnect()


@pytest.mark.run(order=5)
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_broadcast_to_channel_group(data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    group_1 = data_fixture.create_group(users=[user_1, user_2])
    database = data_fixture.create_database_application(group=group_1)
    table_1 = data_fixture.create_database_table(user=user_1)
    table_2 = data_fixture.create_database_table(user=user_2)
    table_3 = data_fixture.create_database_table(database=database)

    communicator_1 = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token_1}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator_1.connect()
    response_1 = await communicator_1.receive_json_from()
    web_socket_id_1 = response_1["web_socket_id"]

    communicator_2 = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token_2}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator_2.connect()
    response_2 = await communicator_2.receive_json_from()
    response_2["web_socket_id"]

    # We don't expect any communicator to receive anything because they didn't join a
    # group.
    await sync_to_async(broadcast_to_channel_group)(
        f"table-{table_1.id}", {"message": "nothing2"}
    )
    await communicator_1.receive_nothing(0.1)
    await communicator_2.receive_nothing(0.1)

    # User 1 is not allowed to join table 2 so we don't expect any response.
    await communicator_1.send_json_to({"page": "table", "table_id": table_2.id})
    await communicator_1.receive_nothing(0.1)

    # Because user 1 did not join table 2 we don't expect anything
    await sync_to_async(broadcast_to_channel_group)(
        f"table-{table_2.id}", {"message": "nothing"}
    )
    await communicator_1.receive_nothing(0.1)
    await communicator_2.receive_nothing(0.1)

    # Join the table page.
    await communicator_1.send_json_to({"page": "table", "table_id": table_1.id})
    response = await communicator_1.receive_json_from(0.1)
    assert response["type"] == "page_add"
    assert response["page"] == "table"
    assert response["parameters"]["table_id"] == table_1.id

    await sync_to_async(broadcast_to_channel_group)(
        f"table-{table_1.id}", {"message": "test"}
    )
    response_1 = await communicator_1.receive_json_from(0.1)
    assert response_1["message"] == "test"
    await communicator_2.receive_nothing(0.1)

    await communicator_1.send_json_to({"page": "table", "table_id": table_3.id})
    response = await communicator_1.receive_json_from(0.1)
    assert response["type"] == "page_discard"
    assert response["page"] == "table"
    assert response["parameters"]["table_id"] == table_1.id
    response = await communicator_1.receive_json_from(0.1)
    assert response["type"] == "page_add"
    assert response["page"] == "table"
    assert response["parameters"]["table_id"] == table_3.id

    await communicator_2.send_json_to({"page": "table", "table_id": table_3.id})
    response = await communicator_2.receive_json_from(0.1)
    assert response["type"] == "page_add"
    assert response["page"] == "table"
    assert response["parameters"]["table_id"] == table_3.id

    await sync_to_async(broadcast_to_channel_group)(
        f"table-{table_3.id}", {"message": "test2"}
    )
    response_1 = await communicator_1.receive_json_from(0.1)
    assert response_1["message"] == "test2"
    response_1 = await communicator_2.receive_json_from(0.1)
    assert response_1["message"] == "test2"

    await sync_to_async(broadcast_to_channel_group)(
        f"table-{table_3.id}", {"message": "test3"}, web_socket_id_1
    )
    await communicator_1.receive_nothing(0.1)
    response_1 = await communicator_2.receive_json_from(0.1)
    assert response_1["message"] == "test3"

    await sync_to_async(broadcast_to_channel_group)(
        f"table-{table_2.id}", {"message": "test4"}
    )
    await communicator_1.receive_nothing(0.1)
    await communicator_2.receive_nothing(0.1)

    assert communicator_1.output_queue.qsize() == 0
    assert communicator_2.output_queue.qsize() == 0

    await communicator_1.disconnect()
    await communicator_2.disconnect()


@pytest.mark.run(order=6)
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_broadcast_to_group(data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    user_3, token_3 = data_fixture.create_user_and_token()
    user_4, token_4 = data_fixture.create_user_and_token()
    group_1 = data_fixture.create_group(users=[user_1, user_2, user_4])
    group_2 = data_fixture.create_group(users=[user_2, user_3])

    communicator_1 = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token_1}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator_1.connect()
    response_1 = await communicator_1.receive_json_from()
    web_socket_id_1 = response_1["web_socket_id"]

    communicator_2 = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token_2}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator_2.connect()
    response_2 = await communicator_2.receive_json_from()
    web_socket_id_2 = response_2["web_socket_id"]

    communicator_3 = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token_3}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator_3.connect()
    await communicator_3.receive_json_from()

    await database_sync_to_async(broadcast_to_group)(group_1.id, {"message": "test"})
    response_1 = await communicator_1.receive_json_from(0.1)
    response_2 = await communicator_2.receive_json_from(0.1)
    await communicator_3.receive_nothing(0.1)

    assert response_1["message"] == "test"
    assert response_2["message"] == "test"

    await database_sync_to_async(broadcast_to_group)(
        group_1.id, {"message": "test2"}, ignore_web_socket_id=web_socket_id_1
    )

    await communicator_1.receive_nothing(0.1)
    response_2 = await communicator_2.receive_json_from(0.1)
    await communicator_3.receive_nothing(0.1)

    assert response_2["message"] == "test2"

    await database_sync_to_async(broadcast_to_group)(
        group_2.id, {"message": "test3"}, ignore_web_socket_id=web_socket_id_2
    )

    await communicator_1.receive_nothing(0.1)
    await communicator_2.receive_nothing(0.1)
    await communicator_3.receive_json_from(0.1)

    assert communicator_1.output_queue.qsize() == 0
    assert communicator_2.output_queue.qsize() == 0
    assert communicator_3.output_queue.qsize() == 0

    await communicator_1.disconnect()
    await communicator_2.disconnect()
    await communicator_3.disconnect()

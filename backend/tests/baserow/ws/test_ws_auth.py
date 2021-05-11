import pytest

from channels.testing import WebsocketCommunicator

from baserow.config.asgi import application

from baserow.ws.auth import get_user


@pytest.mark.run(order=1)
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_get_user(data_fixture):
    user, token = data_fixture.create_user_and_token()

    assert await get_user("random") is None

    u = await get_user(token)
    assert user.id == u.id


@pytest.mark.run(order=2)
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_token_auth_middleware(data_fixture):
    user, token = data_fixture.create_user_and_token()

    communicator = WebsocketCommunicator(application, f"ws/core/")
    connected, subprotocol = await communicator.connect()
    assert connected
    json = await communicator.receive_json_from()
    assert json["type"] == "authentication"
    assert json["success"] is False
    assert json["web_socket_id"] is None
    await communicator.disconnect()

    communicator = WebsocketCommunicator(application, f"ws/core/?jwt_token=random")
    connected, subprotocol = await communicator.connect()
    assert connected
    json = await communicator.receive_json_from()
    assert json["type"] == "authentication"
    assert json["success"] is False
    assert json["web_socket_id"] is not None
    await communicator.disconnect()

    communicator = WebsocketCommunicator(application, f"ws/core/?jwt_token={token}")
    connected, subprotocol = await communicator.connect()
    assert connected
    json = await communicator.receive_json_from()
    assert json["type"] == "authentication"
    assert json["success"] is True
    assert json["web_socket_id"] is not None
    await communicator.disconnect()

    communicator = WebsocketCommunicator(application, f"ws/core/?jwt_token={token}")
    connected, subprotocol = await communicator.connect()
    assert connected
    json = await communicator.receive_json_from()
    assert json["type"] == "authentication"
    assert json["web_socket_id"] is not None
    await communicator.disconnect()

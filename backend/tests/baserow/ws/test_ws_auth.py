import pytest
from channels.testing import WebsocketCommunicator

from baserow.config.asgi import application
from baserow.ws.auth import ANONYMOUS_USER_TOKEN, get_user


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.websockets
async def test_get_user(data_fixture):
    user, token = data_fixture.create_user_and_token()

    assert await get_user("random") is None

    u = await get_user(token)
    assert user.id == u.id

    anonymous_token_user = await get_user(ANONYMOUS_USER_TOKEN)
    assert anonymous_token_user.is_anonymous


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
@pytest.mark.websockets
async def test_token_auth_middleware(data_fixture, settings):
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

    # Test anonymous connections
    communicator = WebsocketCommunicator(
        application, f"ws/core/?jwt_token={ANONYMOUS_USER_TOKEN}"
    )
    connected, subprotocol = await communicator.connect()
    assert connected
    json = await communicator.receive_json_from()
    assert json["type"] == "authentication"
    assert json["success"]
    assert json["web_socket_id"] is not None
    await communicator.disconnect()

    # Test cant connect as anonymous user if feature disabled.
    settings.DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS = True
    communicator = WebsocketCommunicator(
        application, f"ws/core/?jwt_token={ANONYMOUS_USER_TOKEN}"
    )
    connected, subprotocol = await communicator.connect()
    assert connected
    json = await communicator.receive_json_from()
    assert json["type"] == "authentication"
    assert not json["success"]
    await communicator.disconnect()

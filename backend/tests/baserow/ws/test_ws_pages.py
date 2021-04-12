import pytest

from channels.testing import WebsocketCommunicator

from baserow.config.asgi import application


@pytest.mark.run(order=3)
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_join_page(data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user_1)

    communicator_1 = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={token_1}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator_1.connect()
    await communicator_1.receive_json_from()

    # Join the table page.
    await communicator_1.send_json_to({"page": "table", "table_id": table_1.id})
    response = await communicator_1.receive_json_from(0.1)
    assert response["type"] == "page_add"
    assert response["page"] == "table"
    assert response["parameters"]["table_id"] == table_1.id

    # When switching to a not existing page we expect to be discarded from the
    # current page.
    await communicator_1.send_json_to({"page": ""})
    response = await communicator_1.receive_json_from(0.1)
    assert response["type"] == "page_discard"
    assert response["page"] == "table"
    assert response["parameters"]["table_id"] == table_1.id

    # When switching to a not existing page we do not expect the confirmation.
    await communicator_1.send_json_to({"page": "NOT_EXISTING_PAGE"})
    assert communicator_1.output_queue.qsize() == 0
    await communicator_1.disconnect()

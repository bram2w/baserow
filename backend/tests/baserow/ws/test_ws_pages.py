import pytest

from channels.testing import WebsocketCommunicator

from baserow.config.asgi import application
from baserow.ws.auth import ANONYMOUS_USER_TOKEN


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


@pytest.mark.run(order=4)
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_join_page_as_anonymous_user(data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user_1)
    public_grid_view = data_fixture.create_grid_view(user_1, table=table_1, public=True)
    non_public_grid_view = data_fixture.create_grid_view(
        user_1, table=table_1, public=False
    )
    public_form_view_which_cant_be_subbed = data_fixture.create_form_view(
        user_1, table=table_1, public=True
    )

    communicator_1 = WebsocketCommunicator(
        application,
        f"ws/core/?jwt_token={ANONYMOUS_USER_TOKEN}",
        headers=[(b"origin", b"http://localhost")],
    )
    await communicator_1.connect()
    await communicator_1.receive_json_from()

    # Join the public view page.
    await communicator_1.send_json_to({"page": "view", "slug": public_grid_view.slug})
    response = await communicator_1.receive_json_from(0.1)
    assert response["type"] == "page_add"
    assert response["page"] == "view"
    assert response["parameters"]["slug"] == public_grid_view.slug

    # Cant join a table page.
    # When switching to a page where the user cannot join we expect to be discarded from
    # the current page.
    await communicator_1.send_json_to({"page": "table", "table_id": table_1.id})
    response = await communicator_1.receive_json_from(0.1)
    assert response["type"] == "page_discard"
    assert response["page"] == "view"
    assert response["parameters"]["slug"] == public_grid_view.slug

    # Can't join a non public grid view page
    await communicator_1.send_json_to(
        {"page": "view", "slug": non_public_grid_view.slug}
    )
    assert communicator_1.output_queue.qsize() == 0
    await communicator_1.disconnect()

    # Can't join a public form view page as it has
    # `FormViewTypewhen_shared_publicly_requires_realtime_events=False`
    await communicator_1.send_json_to(
        {"page": "view", "slug": public_form_view_which_cant_be_subbed.slug}
    )
    assert communicator_1.output_queue.qsize() == 0
    await communicator_1.disconnect()

    # Can't join an invalid view page
    await communicator_1.send_json_to({"page": "view", "slug": "invalid slug"})
    assert communicator_1.output_queue.qsize() == 0
    await communicator_1.disconnect()

    # Can't join a view page without a slug
    await communicator_1.send_json_to({"page": "view"})
    assert communicator_1.output_queue.qsize() == 0
    await communicator_1.disconnect()

    # Can't join an invalid page
    await communicator_1.send_json_to({"page": ""})
    assert communicator_1.output_queue.qsize() == 0
    await communicator_1.disconnect()

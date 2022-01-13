from unittest.mock import patch, call, ANY

import pytest

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.views.handler import ViewHandler


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_view_filter_created_for_public_view_force_refresh_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    public_view = data_fixture.create_grid_view(user=user, table=table, public=True)
    ViewHandler().create_filter(
        user=user, view=public_view, type_name="equal", value="test", field=field
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view.slug}",
                {"type": "force_view_rows_refresh", "view_id": public_view.slug},
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_view_filter_updated_for_public_view_force_refresh_event_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    public_view = data_fixture.create_grid_view(user=user, table=table, public=True)
    view_filter = data_fixture.create_view_filter(
        user=user, view=public_view, field=field
    )
    ViewHandler().update_filter(user=user, view_filter=view_filter, value="test2")

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view.slug}",
                {"type": "force_view_rows_refresh", "view_id": public_view.slug},
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_view_filter_deleted_for_public_view_force_refresh_event_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    public_view = data_fixture.create_grid_view(user=user, table=table, public=True)
    view_filter = data_fixture.create_view_filter(
        user=user, view=public_view, field=field
    )
    ViewHandler().delete_filter(user=user, view_filter=view_filter)

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view.slug}",
                {"type": "force_view_rows_refresh", "view_id": public_view.slug},
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_field_hidden_in_public_view_field_force_refresh_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    public_grid_view = data_fixture.create_grid_view(table=table, public=True)

    # No public events should be sent to form views
    public_form_view = data_fixture.create_form_view(
        user=user, table=table, public=True
    )
    handler = ViewHandler()
    handler.update_field_options(
        user=user,
        view=public_form_view,
        field_options={str(text_field.id): {"hidden": True}},
    )

    handler.update_field_options(
        user=user,
        view=public_grid_view,
        field_options={str(text_field.id): {"hidden": True}},
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_grid_view.slug}",
                {
                    "type": "force_view_refresh",
                    "view_id": public_grid_view.slug,
                    "fields": [],
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_field_unhidden_in_public_view_force_refresh_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    public_grid_view = data_fixture.create_grid_view(
        table=table, public=True, create_options=False
    )
    data_fixture.create_grid_view_field_option(
        grid_view=public_grid_view, field=text_field, hidden=True
    )
    handler = ViewHandler()

    # No public events should be sent to form views
    public_form_view = data_fixture.create_form_view(
        user=user, table=table, public=True
    )
    handler.update_field_options(
        user=user,
        view=public_form_view,
        field_options={str(text_field.id): {"hidden": False}},
    )
    handler.update_field_options(
        user=user,
        view=public_grid_view,
        field_options={str(text_field.id): {"hidden": False}},
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_grid_view.slug}",
                {
                    "type": "force_view_refresh",
                    "view_id": public_grid_view.slug,
                    "fields": [
                        {
                            "id": text_field.id,
                            "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                            "name": text_field.name,
                            "order": 0,
                            "type": "text",
                            "primary": False,
                            "text_default": "",
                        }
                    ],
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_only_field_options_updated_in_public_grid_view_force_refresh_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_grid_view = data_fixture.create_grid_view(
        table=table, public=True, create_options=False
    )
    data_fixture.create_grid_view_field_option(
        grid_view=public_grid_view, field=visible_field, hidden=False
    )
    data_fixture.create_grid_view_field_option(
        grid_view=public_grid_view, field=hidden_field, hidden=True
    )
    handler = ViewHandler()

    # No public events should be sent to form views
    public_form_view = data_fixture.create_form_view(
        user=user, table=table, public=True
    )
    handler.update_field_options(
        user=user,
        view=public_form_view,
        field_options={
            str(visible_field.id): {"width": 100},
            str(hidden_field.id): {"width": 100},
        },
    )

    handler.update_field_options(
        user=user,
        view=public_grid_view,
        field_options={
            str(visible_field.id): {"width": 100},
            str(hidden_field.id): {"width": 100},
        },
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_grid_view.slug}",
                {
                    "type": "force_view_refresh",
                    "view_id": public_grid_view.slug,
                    "fields": [
                        {
                            "id": visible_field.id,
                            "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                            "name": visible_field.name,
                            "order": 0,
                            "type": "text",
                            "primary": False,
                            "text_default": "",
                        }
                    ],
                },
                None,
            ),
        ]
    )

from unittest.mock import patch

from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext, override_settings

import pytest

from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.ws.views.rows.handler import ViewRealtimeRowsHandler


def _payloads_for_view(mock_broadcast_to_channel_group, slug):
    group_name = f"view-{slug}"
    return [
        call.args[1]
        for call in mock_broadcast_to_channel_group.delay.mock_calls
        if call.args and call.args[0] == group_name
    ]


def _force_rows_refresh(slug):
    return {"type": "force_view_rows_refresh", "view_id": slug}


def _setup_linked_tables(data_fixture, user, rows_a_per_b_row=3, b_rows=1):
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific
    lookup_a = data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), '')"
    )
    rows_b = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "b"}] * b_rows)
        .created_rows
    )
    for row_b in rows_b:
        RowHandler().create_rows(
            user,
            table_a,
            [{link_a_b.db_column: [row_b.id]}] * rows_a_per_b_row,
        )
    return table_a, table_b, primary_b, lookup_a, rows_b


def _create_public_view_with_filter(data_fixture, user, table, field):
    view = data_fixture.create_grid_view(
        user, table=table, public=True, create_options=False
    )
    data_fixture.create_grid_view_field_option(view, field, hidden=False)
    data_fixture.create_view_filter(view=view, field=field, type="contains", value="b")
    return view


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.table.signals.broadcast_to_permitted_users")
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_cascade_over_the_limit_refreshes_the_public_views_wanting_realtime_events(
    mock_broadcast_to_channel_group, mock_broadcast_to_permitted_users, data_fixture
):
    user = data_fixture.create_user()
    table_a, table_b, primary_b, lookup_a, rows_b = _setup_linked_tables(
        data_fixture, user
    )
    filtered_view = _create_public_view_with_filter(
        data_fixture, user, table_a, lookup_a
    )
    unfiltered_view = data_fixture.create_grid_view(
        user, table=table_a, public=True, create_options=False
    )
    private_view = data_fixture.create_grid_view(user, table=table_a, public=False)
    form_view = data_fixture.create_form_view(user, table=table_a, public=True)

    mock_broadcast_to_channel_group.reset_mock()
    mock_broadcast_to_permitted_users.reset_mock()
    with override_settings(DEPENDANT_ROWS_REALTIME_UPDATE_LIMIT=2):
        with transaction.atomic():
            RowHandler().update_rows(
                user, table_b, [{"id": rows_b[0].id, primary_b.db_column: "bb"}]
            )

    for view in (filtered_view, unfiltered_view):
        assert _payloads_for_view(mock_broadcast_to_channel_group, view.slug) == [
            _force_rows_refresh(view.slug)
        ]
    for view in (private_view, form_view):
        assert _payloads_for_view(mock_broadcast_to_channel_group, view.slug) == []
    # Workspace members still get the whole table refreshed.
    mock_broadcast_to_permitted_users.delay.assert_called_once()
    table_payload = mock_broadcast_to_permitted_users.delay.call_args[0][4]
    assert table_payload["table_id"] == table_a.id
    assert table_payload["force_table_refresh"] is True


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_cascades_of_one_transaction_passing_the_limit_together_refresh_public_views(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table_a, table_b, primary_b, lookup_a, rows_b = _setup_linked_tables(
        data_fixture, user, rows_a_per_b_row=3, b_rows=2
    )
    public_view = _create_public_view_with_filter(data_fixture, user, table_a, lookup_a)

    mock_broadcast_to_channel_group.reset_mock()
    with override_settings(DEPENDANT_ROWS_REALTIME_UPDATE_LIMIT=4):
        with transaction.atomic():
            for row_b in rows_b:
                RowHandler().update_rows(
                    user, table_b, [{"id": row_b.id, primary_b.db_column: "bb"}]
                )

    assert _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug) == [
        _force_rows_refresh(public_view.slug)
    ]


@pytest.mark.django_db(transaction=True)
@patch.object(ViewRealtimeRowsHandler, "broadcast_force_rows_refresh_to_views")
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_cascade_within_the_limit_does_not_list_the_views_to_refresh(
    mock_broadcast_to_channel_group, mock_refresh_views, data_fixture
):
    user = data_fixture.create_user()
    table_a, table_b, primary_b, lookup_a, rows_b = _setup_linked_tables(
        data_fixture, user
    )
    public_view = _create_public_view_with_filter(data_fixture, user, table_a, lookup_a)

    mock_broadcast_to_channel_group.reset_mock()
    with override_settings(DEPENDANT_ROWS_REALTIME_UPDATE_LIMIT=3):
        with transaction.atomic():
            RowHandler().update_rows(
                user, table_b, [{"id": rows_b[0].id, primary_b.db_column: "bb"}]
            )

    mock_refresh_views.assert_not_called()
    payload_types = [
        payload["type"]
        for payload in _payloads_for_view(
            mock_broadcast_to_channel_group, public_view.slug
        )
    ]
    assert "force_view_rows_refresh" not in payload_types


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_refreshing_the_views_of_a_table_lists_them_with_one_query(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    public_views = [
        data_fixture.create_grid_view(
            user, table=table, public=True, create_options=False
        )
        for _ in range(3)
    ]
    data_fixture.create_grid_view(user, table=table, public=False)
    # The first call caches the content types the view types are found by.
    ViewRealtimeRowsHandler().broadcast_force_rows_refresh_to_views(table)
    mock_broadcast_to_channel_group.reset_mock()

    with CaptureQueriesContext(connection) as queries:
        ViewRealtimeRowsHandler().broadcast_force_rows_refresh_to_views(table)

    assert len(queries) == 1
    assert mock_broadcast_to_channel_group.delay.call_count == len(public_views)

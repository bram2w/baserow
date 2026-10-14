from unittest.mock import patch

from django.db import transaction
from django.test.utils import override_settings

import pytest

from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.views.handler import ViewHandler
from baserow_enterprise.view_ownership_types import RestrictedViewOwnershipType


def _payloads_for_restricted_view(mock_broadcast_to_channel_group, view_id):
    group_name = f"restricted-view-{view_id}"
    return [
        call.args[1]
        for call in mock_broadcast_to_channel_group.delay.mock_calls
        if call.args and call.args[0] == group_name
    ]


def _payloads_for_public_view(mock_broadcast_to_channel_group, slug):
    group_name = f"view-{slug}"
    return [
        call.args[1]
        for call in mock_broadcast_to_channel_group.delay.mock_calls
        if call.args and call.args[0] == group_name
    ]


def _force_rows_refresh(view_id):
    return {"type": "force_view_rows_refresh", "view_id": view_id}


def _setup_linked_tables(enterprise_data_fixture, user, b_rows=1):
    table_a, table_b, link_a_b = enterprise_data_fixture.create_two_linked_tables(
        user=user
    )
    primary_b = table_b.field_set.get(primary=True).specific
    lookup_a = enterprise_data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), '')"
    )
    rows_b = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "b"}] * b_rows)
        .created_rows
    )
    for row_b in rows_b:
        RowHandler().create_rows(user, table_a, [{link_a_b.db_column: [row_b.id]}] * 3)
    return table_a, table_b, primary_b, lookup_a, rows_b


def _create_restricted_view(enterprise_data_fixture, user, table, **kwargs):
    return enterprise_data_fixture.create_grid_view(
        user,
        table=table,
        ownership_type=RestrictedViewOwnershipType.type,
        create_options=False,
        **kwargs,
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_cascade_over_the_limit_refreshes_the_restricted_views(
    mock_broadcast_to_channel_group, enterprise_data_fixture
):
    user = enterprise_data_fixture.create_user()
    table_a, table_b, primary_b, lookup_a, rows_b = _setup_linked_tables(
        enterprise_data_fixture, user
    )
    filtered_view = _create_restricted_view(enterprise_data_fixture, user, table_a)
    enterprise_data_fixture.create_grid_view_field_option(
        filtered_view, lookup_a, hidden=False
    )
    enterprise_data_fixture.create_view_filter(
        view=filtered_view, field=lookup_a, type="contains", value="b"
    )
    unfiltered_view = _create_restricted_view(enterprise_data_fixture, user, table_a)
    personal_view = enterprise_data_fixture.create_grid_view(user, table=table_a)
    restricted_form_view = enterprise_data_fixture.create_form_view(
        user, table=table_a, ownership_type=RestrictedViewOwnershipType.type
    )
    public_view = enterprise_data_fixture.create_grid_view(
        user, table=table_a, public=True, create_options=False
    )

    mock_broadcast_to_channel_group.reset_mock()
    with override_settings(DEPENDANT_ROWS_REALTIME_UPDATE_LIMIT=2):
        with transaction.atomic():
            RowHandler().update_rows(
                user, table_b, [{"id": rows_b[0].id, primary_b.db_column: "bb"}]
            )

    for view in (filtered_view, unfiltered_view):
        assert _payloads_for_restricted_view(
            mock_broadcast_to_channel_group, view.id
        ) == [_force_rows_refresh(view.id)]
    for view in (personal_view, restricted_form_view):
        assert (
            _payloads_for_restricted_view(mock_broadcast_to_channel_group, view.id)
            == []
        )
    # Publicly shared views are refreshed by the same single listing of the views.
    assert _payloads_for_public_view(
        mock_broadcast_to_channel_group, public_view.slug
    ) == [_force_rows_refresh(public_view.slug)]


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_cascades_of_one_transaction_passing_the_limit_together_refresh_restricted_views(
    mock_broadcast_to_channel_group, enterprise_data_fixture
):
    user = enterprise_data_fixture.create_user()
    table_a, table_b, primary_b, lookup_a, rows_b = _setup_linked_tables(
        enterprise_data_fixture, user, b_rows=2
    )
    restricted_view = _create_restricted_view(enterprise_data_fixture, user, table_a)
    enterprise_data_fixture.create_grid_view_field_option(
        restricted_view, lookup_a, hidden=False
    )
    enterprise_data_fixture.create_view_filter(
        view=restricted_view, field=lookup_a, type="contains", value="b"
    )

    mock_broadcast_to_channel_group.reset_mock()
    with override_settings(DEPENDANT_ROWS_REALTIME_UPDATE_LIMIT=4):
        with transaction.atomic():
            for row_b in rows_b:
                RowHandler().update_rows(
                    user, table_b, [{"id": row_b.id, primary_b.db_column: "bb"}]
                )

    assert _payloads_for_restricted_view(
        mock_broadcast_to_channel_group, restricted_view.id
    ) == [_force_rows_refresh(restricted_view.id)]


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_creating_a_filter_refreshes_the_rows_of_the_restricted_view(
    mock_broadcast_to_channel_group, enterprise_data_fixture
):
    user = enterprise_data_fixture.create_user()
    table = enterprise_data_fixture.create_database_table(user=user)
    field = enterprise_data_fixture.create_text_field(table=table)
    restricted_view = _create_restricted_view(enterprise_data_fixture, user, table)

    mock_broadcast_to_channel_group.reset_mock()
    ViewHandler().create_filter(user, restricted_view, field, "equal", "a")

    assert _payloads_for_restricted_view(
        mock_broadcast_to_channel_group, restricted_view.id
    ) == [_force_rows_refresh(restricted_view.id)]

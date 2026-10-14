from unittest.mock import patch

from django.db import transaction

import pytest

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.ws.rows.tasks import broadcast_dependant_rows_updated
from baserow_enterprise.view_ownership_types import RestrictedViewOwnershipType


def _payloads_for_restricted_view(mock_broadcast_to_channel_group, view_id):
    """The payloads broadcast to a restricted view's page group, in call order."""

    group_name = f"restricted-view-{view_id}"
    return [
        call.args[1]
        for call in mock_broadcast_to_channel_group.delay.mock_calls
        if call.args and call.args[0] == group_name
    ]


def _setup_linked_tables_with_restricted_view(
    enterprise_data_fixture, user, filter_value
):
    table_a, table_b, link_a_b = enterprise_data_fixture.create_two_linked_tables(
        user=user
    )
    primary_b = table_b.field_set.get(primary=True).specific
    lookup_a = enterprise_data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), '')"
    )

    restricted_view = enterprise_data_fixture.create_grid_view(
        user,
        table=table_a,
        ownership_type=RestrictedViewOwnershipType.type,
        create_options=False,
    )
    enterprise_data_fixture.create_grid_view_field_option(
        restricted_view, lookup_a, hidden=False
    )
    enterprise_data_fixture.create_view_filter(
        view=restricted_view, field=lookup_a, type="contains", value=filter_value
    )

    return table_a, table_b, link_a_b, primary_b, lookup_a, restricted_view


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_dependant_row_still_matching_filter_receives_rows_updated_in_restricted_view(
    mock_broadcast_to_channel_group, enterprise_data_fixture
):
    user = enterprise_data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        restricted_view,
    ) = _setup_linked_tables_with_restricted_view(
        enterprise_data_fixture, user, filter_value="keep"
    )

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "keep me"}])
        .created_rows[0]
    )
    row_a1 = (
        RowHandler()
        .create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])
        .created_rows[0]
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "keep me too"}]
        )

    payloads = _payloads_for_restricted_view(
        mock_broadcast_to_channel_group, restricted_view.id
    )
    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["type"] == "rows_updated"
    assert payload["table_id"] == table_a.id
    assert [row["id"] for row in payload["rows"]] == [row_a1.id]
    assert payload["rows"][0][f"field_{lookup_a.id}"] == "keep me too"
    assert payload["rows_before_update"] == [{"id": row_a1.id}]


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_dependant_row_leaving_filter_receives_rows_deleted_in_restricted_view(
    mock_broadcast_to_channel_group, enterprise_data_fixture
):
    user = enterprise_data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        restricted_view,
    ) = _setup_linked_tables_with_restricted_view(
        enterprise_data_fixture, user, filter_value="old"
    )

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "old"}])
        .created_rows[0]
    )
    row_a1 = (
        RowHandler()
        .create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])
        .created_rows[0]
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "new"}]
        )

    payloads = _payloads_for_restricted_view(
        mock_broadcast_to_channel_group, restricted_view.id
    )
    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["type"] == "rows_deleted"
    assert payload["table_id"] == table_a.id
    assert payload["row_ids"] == [row_a1.id]
    assert payload["rows"][0][f"field_{lookup_a.id}"] == "old"


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_dependant_row_entering_filter_receives_rows_created_in_restricted_view(
    mock_broadcast_to_channel_group, enterprise_data_fixture
):
    user = enterprise_data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        restricted_view,
    ) = _setup_linked_tables_with_restricted_view(
        enterprise_data_fixture, user, filter_value="new"
    )

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "old"}])
        .created_rows[0]
    )
    row_a1 = (
        RowHandler()
        .create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])
        .created_rows[0]
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "new"}]
        )

    payloads = _payloads_for_restricted_view(
        mock_broadcast_to_channel_group, restricted_view.id
    )
    # The update comes from the broadcast task, which runs after the commit.
    assert [payload["type"] for payload in payloads] == ["rows_created", "rows_updated"]
    payload = payloads[0]
    assert payload["before_row_id"] is None
    assert [row["id"] for row in payload["rows"]] == [row_a1.id]
    assert payload["rows"][0][f"field_{lookup_a.id}"] == "new"


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_paying_off_an_order_removes_it_from_the_restricted_view(
    mock_broadcast_to_channel_group, enterprise_data_fixture
):
    user = enterprise_data_fixture.create_user()
    orders, payments, orders_payments = (
        enterprise_data_fixture.create_two_linked_tables(user=user)
    )
    payments_primary = payments.field_set.get(primary=True).specific
    total = FieldHandler().create_field(user, orders, "number", name="total")
    amount = FieldHandler().create_field(user, payments, "number", name="amount")
    remaining = FieldHandler().create_field(
        user,
        orders,
        "formula",
        name="remaining",
        formula="field('total') - sum(lookup('link', 'amount'))",
    )
    payments_orders = orders_payments.link_row_related_field

    restricted_view = enterprise_data_fixture.create_grid_view(
        user,
        table=orders,
        ownership_type=RestrictedViewOwnershipType.type,
        create_options=False,
    )
    enterprise_data_fixture.create_grid_view_field_option(
        restricted_view, total, hidden=False
    )
    enterprise_data_fixture.create_grid_view_field_option(
        restricted_view, remaining, hidden=False
    )
    enterprise_data_fixture.create_grid_view_field_option(
        restricted_view, orders_payments, hidden=False
    )
    enterprise_data_fixture.create_view_filter(
        view=restricted_view, field=remaining, type="higher_than", value="0"
    )

    order, other_order = (
        RowHandler()
        .create_rows(user, orders, [{total.db_column: 100}, {total.db_column: 50}])
        .created_rows
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().create_rows(
            user,
            payments,
            [
                {
                    payments_primary.db_column: "SECRET PAYMENT",
                    amount.db_column: 100,
                    payments_orders.db_column: [order.id],
                }
            ],
        )

    payloads = _payloads_for_restricted_view(
        mock_broadcast_to_channel_group, restricted_view.id
    )
    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["type"] == "rows_deleted"
    assert payload["row_ids"] == [order.id]
    # The order leaves with the values the restricted view showed.
    assert payload["rows"][0][remaining.db_column] == "100"
    # The payment that pushed it out was never shown in the view.
    assert orders_payments.db_column not in payload["rows"][0]
    assert "SECRET PAYMENT" not in str(payloads)
    assert other_order.id not in payload["row_ids"]


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_row_leaving_then_reentering_the_restricted_view_is_decided_per_transaction(
    mock_broadcast_to_channel_group, enterprise_data_fixture
):
    user = enterprise_data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        restricted_view,
    ) = _setup_linked_tables_with_restricted_view(
        enterprise_data_fixture, user, filter_value="keep"
    )

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "keep"}])
        .created_rows[0]
    )
    row_a1 = (
        RowHandler()
        .create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])
        .created_rows[0]
    )

    def commit(value):
        mock_broadcast_to_channel_group.reset_mock()
        with transaction.atomic():
            RowHandler().update_rows(
                user, table_b, [{"id": row_b1.id, primary_b.db_column: value}]
            )
        return _payloads_for_restricted_view(
            mock_broadcast_to_channel_group, restricted_view.id
        )

    with patch(
        "baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated"
    ) as mock_task:
        left = commit("gone")
        reentered = commit("keep again")

    # The worker only gets to the first commit's task after the second commit.
    mock_broadcast_to_channel_group.reset_mock()
    broadcast_dependant_rows_updated(**mock_task.delay.call_args_list[0].kwargs)
    lagging_task = _payloads_for_restricted_view(
        mock_broadcast_to_channel_group, restricted_view.id
    )

    assert [payload["type"] for payload in left] == ["rows_deleted"]
    assert left[0]["row_ids"] == [row_a1.id]
    assert left[0]["rows"][0][lookup_a.db_column] == "keep"
    assert [payload["type"] for payload in reentered] == ["rows_created"]
    assert reentered[0]["rows"][0][lookup_a.db_column] == "keep again"
    assert [payload["type"] for payload in lagging_task] == ["rows_updated"]
    assert lagging_task[0]["rows_before_update"] == [{"id": row_a1.id}]
    assert lagging_task[0]["rows"][0][lookup_a.db_column] == "keep again"

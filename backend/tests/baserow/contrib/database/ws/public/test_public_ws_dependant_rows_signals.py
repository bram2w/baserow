import threading
import time
import uuid
from typing import List
from unittest.mock import patch

from django.db import connection, transaction
from django.test import override_settings
from django.test.utils import CaptureQueriesContext

import pytest

from baserow.api.sessions import set_client_undo_redo_action_group_id
from baserow.contrib.database.action.scopes import TableActionScopeType
from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from baserow.contrib.database.fields.dependencies.update_collector import (
    DependantRowsUpdate,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.actions import UpdateRowsActionType
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.ws.rows.signals import DependantRowsBroadcast
from baserow.contrib.database.ws.rows.tasks import broadcast_dependant_rows_updated
from baserow.contrib.database.ws.views.rows.handler import ViewRealtimeRowsHandler
from baserow.core.action.handler import ActionHandler


def _payloads_for_view(mock_broadcast_to_channel_group, slug):
    """The payloads broadcast to a public view's page group, in call order."""

    group_name = f"view-{slug}"
    return [
        call.args[1]
        for call in mock_broadcast_to_channel_group.delay.mock_calls
        if call.args and call.args[0] == group_name
    ]


def _setup_linked_tables_with_public_view(data_fixture, user, filter_value):
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific
    lookup_a = data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), '')"
    )

    public_view = data_fixture.create_grid_view(
        user, table=table_a, public=True, create_options=False
    )
    data_fixture.create_grid_view_field_option(public_view, lookup_a, hidden=False)
    data_fixture.create_view_filter(
        view=public_view, field=lookup_a, type="contains", value=filter_value
    )

    return table_a, table_b, link_a_b, primary_b, lookup_a, public_view


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_dependant_row_still_matching_filter_receives_rows_updated_in_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")

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

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["type"] == "rows_updated"
    assert payload["table_id"] == PUBLIC_PLACEHOLDER_ENTITY_ID
    assert [row["id"] for row in payload["rows"]] == [row_a1.id]
    assert payload["rows"][0][f"field_{lookup_a.id}"] == "keep me too"
    # No pre-cascade values are sent: they might belong to a row the view never
    # showed. The client resolves the before state from its own buffered copy.
    assert payload["rows_before_update"] == [{"id": row_a1.id}]
    # Fields without a grid view option are hidden, so only the visible field leaks.
    assert set(payload["rows"][0].keys()) == {"id", "order", f"field_{lookup_a.id}"}


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_dependant_row_leaving_filter_receives_rows_deleted_in_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="old")

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

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["type"] == "rows_deleted"
    assert payload["table_id"] == PUBLIC_PLACEHOLDER_ENTITY_ID
    assert payload["row_ids"] == [row_a1.id]
    # The pre-cascade values the view showed, restricted to its visible fields.
    assert payload["rows"][0][f"field_{lookup_a.id}"] == "old"
    assert set(payload["rows"][0].keys()) == {"id", "order", f"field_{lookup_a.id}"}


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_dependant_row_entering_filter_receives_rows_created_in_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="new")

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

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    # The update comes from the broadcast task, which runs after the commit.
    assert [payload["type"] for payload in payloads] == ["rows_created", "rows_updated"]
    payload = payloads[0]
    assert payload["before_row_id"] is None
    assert [row["id"] for row in payload["rows"]] == [row_a1.id]
    assert payload["rows"][0][f"field_{lookup_a.id}"] == "new"
    assert set(payload["rows"][0].keys()) == {"id", "order", f"field_{lookup_a.id}"}


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_dependant_row_staying_hidden_gets_no_realtime_event_in_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "hidden"}])
        .created_rows[0]
    )
    RowHandler().create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "still hidden"}]
        )

    assert _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug) == []


def _setup_linked_tables_with_link_filtered_public_view(data_fixture, user):
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific
    lookup_a = data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), '')"
    )

    public_view = data_fixture.create_grid_view(
        user, table=table_a, public=True, create_options=False
    )
    data_fixture.create_grid_view_field_option(public_view, lookup_a, hidden=False)
    data_fixture.create_view_filter(
        view=public_view, field=link_a_b, type="link_row_contains", value="keep"
    )

    return table_a, table_b, link_a_b, primary_b, lookup_a, public_view


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_dependant_row_leaving_link_row_filter_gets_no_rows_deleted_in_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    # Link row values already changed at snapshot time, so the view isn't checked.
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_link_filtered_public_view(data_fixture, user)

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "keep"}])
        .created_rows[0]
    )
    RowHandler().create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "gone"}]
        )

    assert _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug) == []


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_dependant_row_entering_link_row_filter_gets_only_rows_updated_in_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_link_filtered_public_view(data_fixture, user)

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "gone"}])
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
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "keep"}]
        )

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert [payload["type"] for payload in payloads] == ["rows_updated"]
    assert payloads[0]["rows_before_update"] == [{"id": row_a1.id}]
    assert payloads[0]["rows"][0][f"field_{lookup_a.id}"] == "keep"


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_never_visible_row_paid_off_through_a_link_filter_sends_nothing_to_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    # At snapshot time the link exists but remaining > 0: a check would leak it.
    user = data_fixture.create_user()
    orders, payments, orders_payments = data_fixture.create_two_linked_tables(user=user)
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

    public_view = data_fixture.create_grid_view(
        user, table=orders, public=True, create_options=False
    )
    data_fixture.create_grid_view_field_option(public_view, total, hidden=False)
    data_fixture.create_grid_view_field_option(public_view, remaining, hidden=False)
    data_fixture.create_view_filter(
        view=public_view, field=orders_payments, type="not_empty", value=""
    )
    data_fixture.create_view_filter(
        view=public_view, field=remaining, type="higher_than", value="0"
    )

    order = (
        RowHandler().create_rows(user, orders, [{total.db_column: 100}]).created_rows[0]
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().create_rows(
            user,
            payments,
            [{amount.db_column: 100, payments_orders.db_column: [order.id]}],
        )

    order.refresh_from_db()
    assert getattr(order, remaining.db_column) == 0
    assert _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug) == []


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_dependant_rows_leaving_and_staying_in_public_view_are_reconciled(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")

    row_b1, row_b2, row_b3 = (
        RowHandler()
        .create_rows(
            user,
            table_b,
            [
                {primary_b.db_column: "keep"},
                {primary_b.db_column: "keep"},
                {primary_b.db_column: "hidden"},
            ],
        )
        .created_rows
    )
    row_a1, row_a2, row_a3 = (
        RowHandler()
        .create_rows(
            user,
            table_a,
            [
                {link_a_b.db_column: [row_b1.id]},
                {link_a_b.db_column: [row_b2.id]},
                {link_a_b.db_column: [row_b3.id]},
            ],
        )
        .created_rows
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user,
            table_b,
            [
                {"id": row_b1.id, primary_b.db_column: "keep still"},
                {"id": row_b2.id, primary_b.db_column: "dropped"},
                {"id": row_b3.id, primary_b.db_column: "still hidden"},
            ],
        )

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert [payload["type"] for payload in payloads] == ["rows_deleted", "rows_updated"]
    deleted, updated = payloads
    assert deleted["row_ids"] == [row_a2.id]
    assert deleted["rows"][0][f"field_{lookup_a.id}"] == "keep"
    assert [row["id"] for row in updated["rows"]] == [row_a1.id]
    assert updated["rows"][0][f"field_{lookup_a.id}"] == "keep still"
    # row_a3 was never visible, so none of its values reach the view.
    sent_row_ids = {
        row["id"]
        for payload in payloads
        for key in ("rows", "rows_before_update")
        for row in payload.get(key, [])
    }
    assert row_a3.id not in sent_row_ids


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_row_paid_off_leaves_public_view_without_the_new_payment_in_its_link(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    orders, payments, orders_payments = data_fixture.create_two_linked_tables(user=user)
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

    public_view = data_fixture.create_grid_view(
        user, table=orders, public=True, create_options=False
    )
    for field in (total, remaining, orders_payments):
        data_fixture.create_grid_view_field_option(public_view, field, hidden=False)
    data_fixture.create_view_filter(
        view=public_view, field=remaining, type="higher_than", value="0"
    )

    order = (
        RowHandler().create_rows(user, orders, [{total.db_column: 100}]).created_rows[0]
    )
    RowHandler().create_rows(
        user,
        payments,
        [
            {
                payments_primary.db_column: "first payment",
                amount.db_column: 40,
                payments_orders.db_column: [order.id],
            }
        ],
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().create_rows(
            user,
            payments,
            [
                {
                    payments_primary.db_column: "SECRET PAYMENT",
                    amount.db_column: 60,
                    payments_orders.db_column: [order.id],
                }
            ],
        )

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert [payload["type"] for payload in payloads] == ["rows_deleted"]
    assert payloads[0]["row_ids"] == [order.id]
    deleted_row = payloads[0]["rows"][0]
    assert deleted_row[remaining.db_column] == "60"
    # Already holds the new payment at snapshot time, so its real before is unknown.
    assert orders_payments.db_column not in deleted_row
    assert "SECRET PAYMENT" not in str(payloads)


def _setup_never_visible_row_in_public_view(data_fixture, user):
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")
    secret_a = data_fixture.create_text_field(table=table_a, name="secret")
    data_fixture.create_grid_view_field_option(public_view, secret_a, hidden=False)

    with transaction.atomic():
        row_b1 = (
            RowHandler()
            .create_rows(user, table_b, [{primary_b.db_column: "hidden"}])
            .created_rows[0]
        )
    with transaction.atomic():
        row_a1 = (
            RowHandler()
            .create_rows(
                user,
                table_a,
                [{link_a_b.db_column: [row_b1.id], secret_a.db_column: "top secret"}],
            )
            .created_rows[0]
        )
    return table_b, primary_b, row_b1, row_a1, public_view


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_never_visible_row_shown_only_mid_transaction_sends_nothing_to_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table_b, primary_b, row_b1, row_a1, public_view = (
        _setup_never_visible_row_in_public_view(data_fixture, user)
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "keep"}]
        )
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "hidden again"}]
        )

    assert _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug) == []


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_undoing_an_action_group_never_sends_a_never_visible_row_to_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table_b, primary_b, row_b1, row_a1, public_view = (
        _setup_never_visible_row_in_public_view(data_fixture, user)
    )

    set_client_undo_redo_action_group_id(user, str(uuid.uuid4()))
    for value in ("keep", "hidden again"):
        with transaction.atomic():
            UpdateRowsActionType.do(
                user, table_b, [{"id": row_b1.id, primary_b.db_column: value}]
            )
    set_client_undo_redo_action_group_id(user, None)

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        ActionHandler.undo(user, [TableActionScopeType.value(table_b.id)], session_id)

    row_b1.refresh_from_db()
    assert getattr(row_b1, primary_b.db_column) == "hidden"
    assert _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug) == []


@pytest.mark.django_db(transaction=True)
@override_settings(DEPENDANT_ROWS_REALTIME_UPDATE_LIMIT=200)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_never_visible_row_changed_before_its_snapshot_sends_nothing_to_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table_b = data_fixture.create_database_table(database=database)
    x_b = data_fixture.create_text_field(table=table_b, name="x", primary=True)
    table_a = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=table_a, name="primary", primary=True)
    secret_a = data_fixture.create_text_field(table=table_a, name="secret")
    link1, link2, link3 = [
        FieldHandler().create_field(
            user, table_a, "link_row", name=f"link{n}", link_row_table=table_b
        )
        for n in (1, 2, 3)
    ]
    lookup1, lookup2, lookup3 = [
        data_fixture.create_formula_field(
            table=table_a,
            name=f"lookup{n}",
            formula=f"join(lookup('link{n}', 'x'), '')",
        )
        for n in (1, 2, 3)
    ]
    public_view = data_fixture.create_grid_view(
        user, table=table_a, public=True, create_options=False
    )
    for field in (secret_a, lookup1, lookup2, lookup3):
        data_fixture.create_grid_view_field_option(public_view, field, hidden=False)
    data_fixture.create_view_filter(
        view=public_view, field=lookup2, type="contains", value="x2"
    )
    data_fixture.create_view_filter(
        view=public_view, field=lookup3, type="contains", value="x1"
    )

    row_b1 = (
        RowHandler().create_rows(user, table_b, [{x_b.db_column: "x1"}]).created_rows[0]
    )
    RowHandler().create_rows(
        user,
        table_a,
        [
            {link1.db_column: [row_b1.id], link2.db_column: [row_b1.id]}
            for _ in range(150)
        ],
    )
    # Highest id: link2's snapshot reaches it only after the 150 rows link1's took.
    RowHandler().create_rows(
        user,
        table_a,
        [
            {
                link2.db_column: [row_b1.id],
                link3.db_column: [row_b1.id],
                secret_a.db_column: "NEVER VISIBLE",
            }
        ],
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, x_b.db_column: "x2"}]
        )

    assert _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug) == []


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_row_leaving_and_reentering_in_one_transaction_is_only_updated(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")

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

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "gone"}]
        )
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "keep again"}]
        )

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert [payload["type"] for payload in payloads] == ["rows_updated"]
    assert payloads[0]["rows_before_update"] == [{"id": row_a1.id}]
    assert payloads[0]["rows"][0][f"field_{lookup_a.id}"] == "keep again"


def _types_and_lookup_values(payloads, lookup_field):
    return [
        (payload["type"], [row[lookup_field.db_column] for row in payload["rows"]])
        for payload in payloads
    ]


@pytest.mark.parametrize(
    "values,first_commit_payloads,second_commit_payloads,lagging_task_payloads",
    [
        (
            ["keep", "gone", "keep again"],
            [("rows_deleted", ["keep"])],
            [("rows_created", ["keep again"])],
            [("rows_updated", ["keep again"])],
        ),
        (
            ["hidden", "keep", "hidden again"],
            [("rows_created", ["keep"])],
            [("rows_deleted", ["keep"])],
            [],
        ),
        (
            ["keep", "keep too", "gone"],
            [],
            [("rows_deleted", ["keep too"])],
            [],
        ),
    ],
    ids=["left_then_reentered", "entered_then_left", "stayed_then_left"],
)
@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_rows_entering_or_leaving_a_public_view_are_decided_per_transaction(
    mock_broadcast_to_channel_group,
    data_fixture,
    values,
    first_commit_payloads,
    second_commit_payloads,
    lagging_task_payloads,
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")
    initial_value, first_value, second_value = values

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: initial_value}])
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
        return _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)

    with patch(
        "baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated"
    ) as mock_task:
        first_commit = commit(first_value)
        second_commit = commit(second_value)

    # The worker only gets to the first commit's task after the second commit.
    mock_broadcast_to_channel_group.reset_mock()
    broadcast_dependant_rows_updated(**mock_task.delay.call_args_list[0].kwargs)
    lagging_task = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)

    assert _types_and_lookup_values(first_commit, lookup_a) == first_commit_payloads
    assert _types_and_lookup_values(second_commit, lookup_a) == second_commit_payloads
    assert _types_and_lookup_values(lagging_task, lookup_a) == lagging_task_payloads
    for payload in lagging_task:
        assert payload["rows_before_update"] == [{"id": row_a1.id}]


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_dependant_rows_updates_are_not_broadcast_when_table_has_no_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific
    data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), '')"
    )

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "b1"}])
        .created_rows[0]
    )
    RowHandler().create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "renamed"}]
        )

    view_calls = [
        call
        for call in mock_broadcast_to_channel_group.delay.mock_calls
        if call.args and str(call.args[0]).startswith("view-")
    ]
    assert view_calls == []


def _count_broadcast_to_views_queries(data_fixture, user, n_public_views):
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific
    lookup_a = data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), '')"
    )
    for _ in range(n_public_views):
        view = data_fixture.create_grid_view(
            user, table=table_a, public=True, create_options=False
        )
        data_fixture.create_grid_view_field_option(view, lookup_a, hidden=False)
        data_fixture.create_view_filter(
            view=view, field=lookup_a, type="contains", value="keep"
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

    model = table_a.get_model()
    rows = list(model.objects.filter(id__in=[row_a1.id]).enhance_by_fields())
    serialized_rows = get_row_serializer_class(model, RowSerializer, is_response=True)(
        rows, many=True
    ).data

    with CaptureQueriesContext(connection) as captured:
        ViewRealtimeRowsHandler().broadcast_dependant_rows_updated_to_views(
            table_a, model, rows, serialized_rows, [lookup_a.id]
        )
    return len(captured.captured_queries)


@pytest.mark.django_db
def test_broadcast_to_views_is_one_query_without_views_and_flat_across_views(
    data_fixture,
):
    user = data_fixture.create_user()

    # No public/restricted view: a single lookup that finds none, then nothing.
    assert _count_broadcast_to_views_queries(data_fixture, user, 0) == 1

    # The per-row-batch work is fixed, so adding more views must not add queries.
    one_view = _count_broadcast_to_views_queries(data_fixture, user, 1)
    three_views = _count_broadcast_to_views_queries(data_fixture, user, 3)
    assert one_view == three_views


def _count_cascade_update_queries(data_fixture, user, n_public_views):
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific
    lookup_a = data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), '')"
    )
    for _ in range(n_public_views):
        view = data_fixture.create_grid_view(
            user, table=table_a, public=True, create_options=False
        )
        data_fixture.create_view_filter(
            view=view, field=lookup_a, type="contains", value="keep"
        )

    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "keep"}])
        .created_rows[0]
    )
    RowHandler().create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])

    with CaptureQueriesContext(connection) as captured:
        RowHandler().force_update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "keep it"}]
        )
    return len(captured.captured_queries)


@pytest.mark.django_db
def test_cascade_before_visibility_queries_are_flat_across_checked_views(
    data_fixture,
):
    user = data_fixture.create_user()

    # One views lookup per table and one visibility query, whatever the views.
    one_view = _count_cascade_update_queries(data_fixture, user, 1)
    three_views = _count_cascade_update_queries(data_fixture, user, 3)
    assert one_view == three_views


@pytest.mark.django_db
def test_visibility_changes_skip_a_view_whose_before_visibility_is_unknown(
    data_fixture,
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        checked_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")
    snapshot_row_checker = ViewRealtimeRowsHandler().get_checked_views_row_checker(
        table_a, table_a.get_model()
    )
    view_added_after_the_snapshot = data_fixture.create_grid_view(
        user, table=table_a, public=True, create_options=False
    )
    data_fixture.create_view_filter(
        view=view_added_after_the_snapshot,
        field=lookup_a,
        type="contains",
        value="keep",
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

    visibility_changes = (
        ViewRealtimeRowsHandler().get_dependant_rows_visibility_changes(
            DependantRowsUpdate(
                table=table_a,
                row_ids=[row_a1.id],
                field_ids=[lookup_a.id],
                requires_refresh=False,
                before_rows={row_a1.id: {"id": row_a1.id, lookup_a.db_column: "x"}},
                before_visible_view_ids={row_a1.id: set()},
                before_checked_view_ids={checked_view.id},
                checked_views_row_checker=snapshot_row_checker,
            )
        )
    )

    assert [(view.id, payload["type"]) for view, payload in visibility_changes] == [
        (checked_view.id, "rows_created")
    ]


def _count_visibility_changes_queries(data_fixture, user, n_entering_rows, n_views):
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific
    lookup_a = data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), '')"
    )
    views = []
    for _ in range(n_views):
        view = data_fixture.create_grid_view(
            user, table=table_a, public=True, create_options=False
        )
        data_fixture.create_grid_view_field_option(view, lookup_a, hidden=False)
        data_fixture.create_view_filter(
            view=view, field=lookup_a, type="contains", value="keep"
        )
        views.append(view)

    row_b_keep, row_b_gone = (
        RowHandler()
        .create_rows(
            user,
            table_b,
            [{primary_b.db_column: "keep"}, {primary_b.db_column: "gone"}],
        )
        .created_rows
    )
    leaving_row, *entering_rows = (
        RowHandler()
        .create_rows(
            user,
            table_a,
            [{link_a_b.db_column: [row_b_gone.id]}]
            + [{link_a_b.db_column: [row_b_keep.id]} for _ in range(n_entering_rows)],
        )
        .created_rows
    )
    view_ids = {view.id for view in views}
    rows = [leaving_row, *entering_rows]
    update = DependantRowsUpdate(
        table=table_a,
        row_ids=[row.id for row in rows],
        field_ids=[lookup_a.id],
        requires_refresh=False,
        before_rows={
            row.id: {"id": row.id, "order": "1", lookup_a.db_column: "before"}
            for row in rows
        },
        before_visible_view_ids={
            leaving_row.id: view_ids,
            **{row.id: set() for row in entering_rows},
        },
        before_checked_view_ids=view_ids,
        checked_views_row_checker=ViewRealtimeRowsHandler().get_checked_views_row_checker(
            table_a, table_a.get_model()
        ),
    )

    with CaptureQueriesContext(connection) as captured:
        visibility_changes = (
            ViewRealtimeRowsHandler().get_dependant_rows_visibility_changes(update)
        )
    assert [
        payload["type"]
        for view, payload in visibility_changes
        if view.id == views[0].id
    ] == ["rows_deleted", "rows_created"]
    return len(captured.captured_queries)


@pytest.mark.django_db
def test_visibility_changes_queries_are_flat_across_rows_and_views(
    data_fixture,
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    handler = ViewRealtimeRowsHandler()

    with CaptureQueriesContext(connection) as captured:
        handler.get_dependant_rows_visibility_changes(
            DependantRowsUpdate(
                table=table,
                row_ids=[1],
                field_ids=[1],
                requires_refresh=False,
                before_rows={1: {"id": 1}},
                before_visible_view_ids={1: set()},
            )
        )
        handler.get_dependant_rows_visibility_changes(
            DependantRowsUpdate(
                table=table,
                row_ids=[1],
                field_ids=[1],
                requires_refresh=False,
                before_checked_view_ids={1},
            )
        )
    assert len(captured.captured_queries) == 0

    # Warms up the process-wide caches, like the content types one.
    _count_visibility_changes_queries(data_fixture, user, 1, 1)
    one_row_one_view = _count_visibility_changes_queries(data_fixture, user, 1, 1)
    assert _count_visibility_changes_queries(data_fixture, user, 3, 1) == (
        one_row_one_view
    )
    assert _count_visibility_changes_queries(data_fixture, user, 1, 3) == (
        one_row_one_view
    )


def _setup_row_in_public_view_filtered_on_lookup_and_status(data_fixture, user):
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")
    status_a = data_fixture.create_text_field(table=table_a, name="status")
    data_fixture.create_view_filter(
        view=public_view, field=status_a, type="equal", value="on"
    )
    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "keep"}])
        .created_rows[0]
    )
    row_a1 = (
        RowHandler()
        .create_rows(
            user,
            table_a,
            [{link_a_b.db_column: [row_b1.id], status_a.db_column: "on"}],
        )
        .created_rows[0]
    )
    return table_a, table_b, primary_b, status_a, row_b1, row_a1, public_view


def _types_entering_or_leaving(payloads):
    return [
        payload["type"]
        for payload in payloads
        if payload["type"] in ("rows_created", "rows_deleted")
    ]


@pytest.mark.parametrize(
    "operations,expected_types",
    [
        ([("cascade", "keep too"), ("direct", "off")], ["rows_deleted"]),
        ([("direct", "off"), ("cascade", "keep too")], ["rows_deleted"]),
        (
            [("cascade", "keep too"), ("direct", "off"), ("cascade", "keep again")],
            ["rows_deleted"],
        ),
        (
            [("cascade", "gone"), ("direct", "off"), ("cascade", "keep")],
            ["rows_deleted"],
        ),
        (
            [
                ("cascade", "gone"),
                ("direct", "off"),
                ("direct", "on"),
                ("cascade", "keep"),
            ],
            [],
        ),
        (
            [
                ("cascade", "keep too"),
                ("direct", "off"),
                ("direct", "on"),
                ("cascade", "gone"),
            ],
            ["rows_deleted", "rows_created", "rows_deleted"],
        ),
    ],
    ids=[
        "cascade_then_direct",
        "direct_then_cascade",
        "cascade_direct_cascade",
        "left_by_cascade_then_direct_and_cascade",
        "direct_updates_sending_nothing_keep_the_cascades_merged",
        "left_reentered_and_left_again_across_direct_updates",
    ],
)
@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_cascades_and_direct_updates_of_a_row_in_one_transaction_send_each_change_once(
    mock_broadcast_to_channel_group, data_fixture, operations, expected_types
):
    user = data_fixture.create_user()
    table_a, table_b, primary_b, status_a, row_b1, row_a1, public_view = (
        _setup_row_in_public_view_filtered_on_lookup_and_status(data_fixture, user)
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        for kind, value in operations:
            if kind == "cascade":
                RowHandler().update_rows(
                    user, table_b, [{"id": row_b1.id, primary_b.db_column: value}]
                )
            else:
                RowHandler().update_rows(
                    user, table_a, [{"id": row_a1.id, status_a.db_column: value}]
                )

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert _types_entering_or_leaving(payloads) == expected_types


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_undoing_a_direct_and_a_cascading_action_sends_one_rows_deleted(
    mock_broadcast_to_channel_group, data_fixture
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table_a, table_b, primary_b, status_a, row_b1, row_a1, public_view = (
        _setup_row_in_public_view_filtered_on_lookup_and_status(data_fixture, user)
    )
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_a, [{"id": row_a1.id, status_a.db_column: "off"}]
        )

    set_client_undo_redo_action_group_id(user, str(uuid.uuid4()))
    with transaction.atomic():
        UpdateRowsActionType.do(
            user, table_a, [{"id": row_a1.id, status_a.db_column: "on"}]
        )
    with transaction.atomic():
        UpdateRowsActionType.do(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "keep too"}]
        )
    set_client_undo_redo_action_group_id(user, None)

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        ActionHandler.undo(
            user,
            [
                TableActionScopeType.value(table_a.id),
                TableActionScopeType.value(table_b.id),
            ],
            session_id,
        )

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert _types_entering_or_leaving(payloads) == ["rows_deleted"]
    assert payloads[0]["row_ids"] == [row_a1.id]


def _wait_until_another_connection_waits_for_a_lock() -> None:
    with connection.cursor() as cursor:
        for _ in range(200):
            cursor.execute(
                "SELECT 1 FROM pg_stat_activity WHERE datname = current_database() "
                "AND wait_event_type = 'Lock' AND pid <> pg_backend_pid()"
            )
            if cursor.fetchone():
                return
            time.sleep(0.05)
    raise AssertionError("No connection waited for a lock.")


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_concurrent_cascades_into_a_row_send_one_rows_deleted(
    mock_broadcast_to_channel_group, mock_broadcast_task, data_fixture
):
    user = data_fixture.create_user()
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific
    lookup_a = data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), ',')"
    )
    public_view = data_fixture.create_grid_view(
        user, table=table_a, public=True, create_options=False
    )
    data_fixture.create_grid_view_field_option(public_view, lookup_a, hidden=False)
    data_fixture.create_view_filter(
        view=public_view, field=lookup_a, type="contains_not", value="gone"
    )
    row_b1, row_b2 = (
        RowHandler()
        .create_rows(
            user,
            table_b,
            [{primary_b.db_column: "keep"}, {primary_b.db_column: "keep"}],
        )
        .created_rows
    )
    row_a1 = (
        RowHandler()
        .create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id, row_b2.id]}])
        .created_rows[0]
    )

    first_cascaded = threading.Event()
    errors = []

    def first_transaction():
        try:
            with transaction.atomic():
                RowHandler().update_rows(
                    user, table_b, [{"id": row_b1.id, primary_b.db_column: "gone"}]
                )
                first_cascaded.set()
                # Commits only once the second cascade waits for the row lock.
                _wait_until_another_connection_waits_for_a_lock()
        except Exception as exc:
            errors.append(exc)
        finally:
            connection.close()

    mock_broadcast_to_channel_group.reset_mock()
    thread = threading.Thread(target=first_transaction)
    thread.start()
    assert first_cascaded.wait(10)
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b2.id, primary_b.db_column: "gone too"}]
        )
    thread.join(10)

    assert errors == []
    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert _types_entering_or_leaving(payloads) == ["rows_deleted"]
    assert payloads[0]["row_ids"] == [row_a1.id]
    assert payloads[0]["rows"][0][lookup_a.db_column] == "keep,keep"


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_a_late_cascade_broadcast_sends_the_changes_of_its_own_transaction(
    mock_broadcast_to_channel_group, mock_broadcast_task, data_fixture
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")
    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "keep"}])
        .created_rows[0]
    )
    RowHandler().create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])

    late_broadcasts = []
    mock_broadcast_to_channel_group.reset_mock()
    with patch.object(
        DependantRowsBroadcast, "__call__", lambda self: late_broadcasts.append(self)
    ):
        with transaction.atomic():
            RowHandler().update_rows(
                user, table_b, [{"id": row_b1.id, primary_b.db_column: "keep too"}]
            )
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "gone"}]
        )
    late_broadcasts[0]()

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert _types_entering_or_leaving(payloads) == ["rows_deleted"]
    assert payloads[0]["rows"][0][lookup_a.db_column] == "keep too"


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_a_late_rows_created_never_carries_values_of_a_later_commit(
    mock_broadcast_to_channel_group, mock_broadcast_task, data_fixture
):
    user = data_fixture.create_user()
    table_a, table_b, primary_b, status_a, row_b1, row_a1, public_view = (
        _setup_row_in_public_view_filtered_on_lookup_and_status(data_fixture, user)
    )
    secret_a = data_fixture.create_text_field(table=table_a, name="secret")
    data_fixture.create_grid_view_field_option(public_view, secret_a, hidden=False)
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "gone"}]
        )

    late_broadcasts = []
    mock_broadcast_to_channel_group.reset_mock()
    with patch.object(
        DependantRowsBroadcast, "__call__", lambda self: late_broadcasts.append(self)
    ):
        with transaction.atomic():
            RowHandler().update_rows(
                user, table_b, [{"id": row_b1.id, primary_b.db_column: "keep"}]
            )
    with transaction.atomic():
        RowHandler().update_rows(
            user,
            table_a,
            [
                {
                    "id": row_a1.id,
                    status_a.db_column: "off",
                    secret_a.db_column: "SECRET",
                }
            ],
        )
    late_broadcasts[0]()

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert _types_entering_or_leaving(payloads) == ["rows_deleted", "rows_created"]
    assert payloads[1]["rows"][0][secret_a.db_column] is None
    assert "SECRET" not in str(payloads)


@pytest.mark.django_db(transaction=True)
@patch("baserow.contrib.database.ws.rows.signals.broadcast_dependant_rows_updated")
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_a_cascade_evaluates_the_checked_views_with_one_row_checker(
    mock_broadcast_to_channel_group, mock_broadcast_task, data_fixture
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")
    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "keep"}])
        .created_rows[0]
    )
    RowHandler().create_rows(user, table_a, [{link_a_b.db_column: [row_b1.id]}])

    mock_broadcast_to_channel_group.reset_mock()
    with patch.object(
        ViewRealtimeRowsHandler,
        "get_checked_views_row_checker",
        autospec=True,
        side_effect=ViewRealtimeRowsHandler.get_checked_views_row_checker,
    ) as spy:
        with transaction.atomic():
            RowHandler().update_rows(
                user, table_b, [{"id": row_b1.id, primary_b.db_column: "gone"}]
            )

    assert spy.call_count == 1
    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert _types_entering_or_leaving(payloads) == ["rows_deleted"]


def _locks_rows_of(table, sqls: List[str]) -> bool:
    return any(
        f'FOR UPDATE OF "{table.get_database_table_name()}"' in sql for sql in sqls
    )


def _capture_cascade_queries(data_fixture, user, status_filtered: bool) -> List[str]:
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific
    data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'primary'), '')"
    )
    status_a = data_fixture.create_text_field(table=table_a, name="status")
    if status_filtered:
        view = data_fixture.create_grid_view(
            user, table=table_a, public=True, create_options=False
        )
        data_fixture.create_view_filter(
            view=view, field=status_a, type="equal", value="on"
        )
    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "keep"}])
        .created_rows[0]
    )
    RowHandler().create_rows(
        user, table_a, [{link_a_b.db_column: [row_b1.id], status_a.db_column: "on"}]
    )

    with CaptureQueriesContext(connection) as captured:
        RowHandler().force_update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "renamed"}]
        )
    sqls = [query["sql"] for query in captured.captured_queries]
    assert not _locks_rows_of(table_a, sqls)
    return sqls


@pytest.mark.django_db
def test_a_view_filtering_only_fields_a_cascade_cant_change_costs_nothing(
    data_fixture,
):
    user = data_fixture.create_user()
    _capture_cascade_queries(data_fixture, user, status_filtered=False)

    without_view = _capture_cascade_queries(data_fixture, user, status_filtered=False)
    with_status_view = _capture_cascade_queries(
        data_fixture, user, status_filtered=True
    )

    assert len(with_status_view) == len(without_view)


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_a_cascade_two_levels_deep_removes_a_paid_off_order_from_the_public_view(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    orders, payments, orders_payments = data_fixture.create_two_linked_tables(user=user)
    total = FieldHandler().create_field(user, orders, "number", name="total")
    amount = FieldHandler().create_field(user, payments, "number", name="amount")
    FieldHandler().create_field(
        user, orders, "formula", name="paid", formula="sum(lookup('link', 'amount'))"
    )
    remaining = FieldHandler().create_field(
        user,
        orders,
        "formula",
        name="remaining",
        formula="field('total') - field('paid')",
    )
    payments_orders = orders_payments.link_row_related_field

    public_view = data_fixture.create_grid_view(
        user, table=orders, public=True, create_options=False
    )
    for field in (total, remaining):
        data_fixture.create_grid_view_field_option(public_view, field, hidden=False)
    data_fixture.create_view_filter(
        view=public_view, field=remaining, type="higher_than", value="0"
    )
    order = (
        RowHandler().create_rows(user, orders, [{total.db_column: 100}]).created_rows[0]
    )
    payment = (
        RowHandler()
        .create_rows(
            user,
            payments,
            [{amount.db_column: 40, payments_orders.db_column: [order.id]}],
        )
        .created_rows[0]
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, payments, [{"id": payment.id, amount.db_column: 100}]
        )

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert _types_entering_or_leaving(payloads) == ["rows_deleted"]
    [deleted] = [payload for payload in payloads if payload["type"] == "rows_deleted"]
    assert deleted["row_ids"] == [order.id]
    assert deleted["rows"][0][remaining.db_column] == "60"


def _create_third_table_linked_from(data_fixture, user, table_a):
    table_c = data_fixture.create_database_table(
        database=table_a.database, name="table_c"
    )
    primary_c = data_fixture.create_text_field(
        table=table_c, name="primary", primary=True
    )
    link_a_c = FieldHandler().create_field(
        user, table_a, "link_row", name="link_c", link_row_table=table_c
    )
    return table_c, primary_c, link_a_c


@pytest.mark.django_db
def test_a_cascade_into_a_lookup_no_view_filters_on_takes_no_lock(data_fixture):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")
    table_c, primary_c, link_a_c = _create_third_table_linked_from(
        data_fixture, user, table_a
    )
    data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link_c', 'primary'), '')"
    )
    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "keep"}])
        .created_rows[0]
    )
    row_c1 = (
        RowHandler()
        .create_rows(user, table_c, [{primary_c.db_column: "c"}])
        .created_rows[0]
    )
    RowHandler().create_rows(
        user,
        table_a,
        [{link_a_b.db_column: [row_b1.id], link_a_c.db_column: [row_c1.id]}],
    )

    with (
        patch.object(
            ViewRealtimeRowsHandler,
            "get_checked_views_row_checker",
            autospec=True,
            side_effect=ViewRealtimeRowsHandler.get_checked_views_row_checker,
        ) as row_checker_spy,
        CaptureQueriesContext(connection) as captured,
    ):
        RowHandler().force_update_rows(
            user, table_c, [{"id": row_c1.id, primary_c.db_column: "c renamed"}]
        )

    assert row_checker_spy.call_count == 0
    sqls = [query["sql"] for query in captured.captured_queries]
    assert not _locks_rows_of(table_a, sqls)


@pytest.mark.parametrize(
    "filtered_link,expected_types",
    [("unchanged_link", ["rows_deleted"]), ("changed_link", [])],
)
@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_a_view_filtering_on_a_link_is_decided_unless_the_cascade_changed_it(
    mock_broadcast_to_channel_group, data_fixture, filtered_link, expected_types
):
    user = data_fixture.create_user()
    (
        table_a,
        table_b,
        link_a_b,
        primary_b,
        lookup_a,
        public_view,
    ) = _setup_linked_tables_with_public_view(data_fixture, user, filter_value="keep")
    table_c, primary_c, link_a_c = _create_third_table_linked_from(
        data_fixture, user, table_a
    )
    for field in (link_a_b, link_a_c):
        data_fixture.create_grid_view_field_option(public_view, field, hidden=False)
    data_fixture.create_view_filter(
        view=public_view,
        field=link_a_c if filtered_link == "unchanged_link" else link_a_b,
        type="not_empty",
        value="",
    )
    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "keep"}])
        .created_rows[0]
    )
    row_c1 = (
        RowHandler()
        .create_rows(user, table_c, [{primary_c.db_column: "shown"}])
        .created_rows[0]
    )
    row_a1 = (
        RowHandler()
        .create_rows(
            user,
            table_a,
            [{link_a_b.db_column: [row_b1.id], link_a_c.db_column: [row_c1.id]}],
        )
        .created_rows[0]
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "gone"}]
        )

    payloads = _payloads_for_view(mock_broadcast_to_channel_group, public_view.slug)
    assert _types_entering_or_leaving(payloads) == expected_types
    assert "gone" not in str(payloads)
    if expected_types:
        [deleted] = [p for p in payloads if p["type"] == "rows_deleted"]
        assert deleted["row_ids"] == [row_a1.id]
        [deleted_row] = deleted["rows"]
        assert [linked["value"] for linked in deleted_row[link_a_c.db_column]] == [
            "shown"
        ]
        # Already shows the rename at snapshot time, so its before value is unknown.
        assert link_a_b.db_column not in deleted_row


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_a_link_changed_by_an_earlier_closed_cascade_keeps_its_view_undecided(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table_a, table_b, link_a_b = data_fixture.create_two_linked_tables(user=user)
    primary_b = table_b.field_set.get(primary=True).specific
    x_b = data_fixture.create_text_field(table=table_b, name="x")
    lookup_x = data_fixture.create_formula_field(
        table=table_a, formula="join(lookup('link', 'x'), '')"
    )
    status_a = data_fixture.create_text_field(table=table_a, name="status")
    view_v = data_fixture.create_grid_view(
        user, table=table_a, public=True, create_options=False
    )
    data_fixture.create_view_filter(
        view=view_v, field=link_a_b, type="link_row_contains", value="new"
    )
    data_fixture.create_view_filter(
        view=view_v, field=lookup_x, type="contains", value="on"
    )
    view_w = data_fixture.create_grid_view(
        user, table=table_a, public=True, create_options=False
    )
    data_fixture.create_view_filter(
        view=view_w, field=status_a, type="equal", value="on"
    )
    row_b1 = (
        RowHandler()
        .create_rows(user, table_b, [{primary_b.db_column: "old", x_b.db_column: "on"}])
        .created_rows[0]
    )
    row_a3 = (
        RowHandler()
        .create_rows(
            user,
            table_a,
            [{link_a_b.db_column: [row_b1.id], status_a.db_column: "on"}],
        )
        .created_rows[0]
    )

    mock_broadcast_to_channel_group.reset_mock()
    with transaction.atomic():
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, primary_b.db_column: "new"}]
        )
        RowHandler().update_rows(
            user, table_a, [{"id": row_a3.id, status_a.db_column: "off"}]
        )
        RowHandler().update_rows(
            user, table_b, [{"id": row_b1.id, x_b.db_column: "off"}]
        )

    w_payloads = _payloads_for_view(mock_broadcast_to_channel_group, view_w.slug)
    assert _types_entering_or_leaving(w_payloads) == ["rows_deleted"]
    v_payloads = _payloads_for_view(mock_broadcast_to_channel_group, view_v.slug)
    assert _types_entering_or_leaving(v_payloads) == []

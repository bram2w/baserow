from unittest.mock import patch, call, ANY

import pytest
from django.db import transaction

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.views.handler import ViewHandler, PublicViewRows
from baserow.core.trash.handler import TrashHandler
from baserow.contrib.database.trash.models import TrashedRows


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_row_created_public_views_receive_restricted_row_created_ws_event(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_view_only_showing_one_field = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    public_view_showing_all_fields = data_fixture.create_grid_view(
        user, table=table, public=True, order=1
    )
    # No public events should be sent to this form view
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_only_showing_one_field, hidden_field, hidden=True
    )
    row = RowHandler().create_row(
        user=user,
        table=table,
        values={
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "Hidden",
        },
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_only_showing_one_field.slug}",
                {
                    "type": "row_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row": {
                        "id": row.id,
                        "order": "1.00000000000000000000",
                        # Only the visible field should be sent
                        f"field_{visible_field.id}": "Visible",
                    },
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
            call(
                f"view-{public_view_showing_all_fields.slug}",
                {
                    "type": "row_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row": {
                        "id": row.id,
                        "order": "1.00000000000000000000",
                        f"field_{visible_field.id}": "Visible",
                        # This field is not hidden for this public view and so should be
                        # included
                        f"field_{hidden_field.id}": "Hidden",
                    },
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_row_created_public_views_receive_row_created_only_when_filters_match(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_view_showing_row = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    public_view_hiding_row = data_fixture.create_grid_view(
        user, table=table, public=True, order=1
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_showing_row, hidden_field, hidden=True
    )
    data_fixture.create_grid_view_field_option(
        public_view_hiding_row, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=visible_field, type="equal", value="Visible"
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=hidden_field, type="equal", value="Not Match"
    )

    # Match
    data_fixture.create_view_filter(
        view=public_view_showing_row, field=visible_field, type="equal", value="Visible"
    )
    # Match
    data_fixture.create_view_filter(
        view=public_view_showing_row, field=hidden_field, type="equal", value="Hidden"
    )

    row = RowHandler().create_row(
        user=user,
        table=table,
        values={
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "Hidden",
        },
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_showing_row.slug}",
                {
                    "type": "row_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row": {
                        "id": row.id,
                        "order": "1.00000000000000000000",
                        # Only the visible field should be sent
                        f"field_{visible_field.id}": "Visible",
                    },
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_batch_rows_created_public_views_receive_restricted_row_created_ws_event(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_view_only_showing_one_field = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    public_view_showing_all_fields = data_fixture.create_grid_view(
        user, table=table, public=True, order=1
    )
    # No public events should be sent to this form view
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_only_showing_one_field, hidden_field, hidden=True
    )

    rows_to_create = [
        {f"field_{visible_field.id}": "Visible", f"field_{hidden_field.id}": "Hidden"},
        {f"field_{visible_field.id}": "Visible", f"field_{hidden_field.id}": "Hidden"},
    ]

    rows = RowHandler().create_rows(
        user=user,
        table=table,
        rows_values=rows_to_create,
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_only_showing_one_field.slug}",
                {
                    "type": "rows_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "rows": [
                        {
                            "id": rows[0].id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                        {
                            "id": rows[1].id,
                            "order": "2.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
            call(
                f"view-{public_view_showing_all_fields.slug}",
                {
                    "type": "rows_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "rows": [
                        {
                            "id": rows[0].id,
                            "order": "1.00000000000000000000",
                            f"field_{visible_field.id}": "Visible",
                            # This field is not hidden for this public view
                            # and so should be included
                            f"field_{hidden_field.id}": "Hidden",
                        },
                        {
                            "id": rows[1].id,
                            "order": "2.00000000000000000000",
                            f"field_{visible_field.id}": "Visible",
                            # This field is not hidden for this public view
                            # and so should be included
                            f"field_{hidden_field.id}": "Hidden",
                        },
                    ],
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_batch_rows_created_public_views_receive_row_created_when_filters_match(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_view_showing_row = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    public_view_hiding_row = data_fixture.create_grid_view(
        user, table=table, public=True, order=1
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_showing_row, hidden_field, hidden=True
    )
    data_fixture.create_grid_view_field_option(
        public_view_hiding_row, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=visible_field, type="equal", value="Visible"
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=hidden_field, type="equal", value="Not Match"
    )

    # Match
    data_fixture.create_view_filter(
        view=public_view_showing_row, field=visible_field, type="equal", value="Visible"
    )

    rows_to_create = [
        {f"field_{visible_field.id}": "Visible", f"field_{hidden_field.id}": "Hidden"},
        {f"field_{visible_field.id}": "Visible", f"field_{hidden_field.id}": "Hidden"},
    ]

    rows = RowHandler().create_rows(
        user=user,
        table=table,
        rows_values=rows_to_create,
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_showing_row.slug}",
                {
                    "type": "rows_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "rows": [
                        {
                            "id": rows[0].id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                        {
                            "id": rows[1].id,
                            "order": "2.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_row_deleted_public_views_receive_restricted_row_deleted_ws_event(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_view_only_showing_one_field = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    public_view_showing_all_fields = data_fixture.create_grid_view(
        user, table=table, public=True, order=1
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_only_showing_one_field, hidden_field, hidden=True
    )
    model = table.get_model()
    row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "Hidden",
        },
    )
    RowHandler().delete_row_by_id(user, table, row.id, model)

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_only_showing_one_field.slug}",
                {
                    "type": "row_deleted",
                    "row_id": row.id,
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row": {
                        "id": row.id,
                        "order": "1.00000000000000000000",
                        # Only the visible field should be sent
                        f"field_{visible_field.id}": "Visible",
                    },
                },
                None,
            ),
            call(
                f"view-{public_view_showing_all_fields.slug}",
                {
                    "type": "row_deleted",
                    "row_id": row.id,
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row": {
                        "id": row.id,
                        "order": "1.00000000000000000000",
                        f"field_{visible_field.id}": "Visible",
                        # This field is not hidden for this public view
                        # and so should be included
                        f"field_{hidden_field.id}": "Hidden",
                    },
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_row_deleted_public_views_receive_row_deleted_only_when_filters_match(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_view_showing_row = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    public_view_hiding_row = data_fixture.create_grid_view(
        user, table=table, public=True, order=1
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_showing_row, hidden_field, hidden=True
    )
    data_fixture.create_grid_view_field_option(
        public_view_hiding_row, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=visible_field, type="equal", value="Visible"
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=hidden_field, type="equal", value="Not Match"
    )

    # Match
    data_fixture.create_view_filter(
        view=public_view_showing_row, field=visible_field, type="equal", value="Visible"
    )
    # Match
    data_fixture.create_view_filter(
        view=public_view_showing_row, field=hidden_field, type="equal", value="Hidden"
    )

    model = table.get_model()
    row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "Hidden",
        },
    )
    RowHandler().delete_row_by_id(user, table, row.id, model)

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_showing_row.slug}",
                {
                    "type": "row_deleted",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row_id": row.id,
                    "row": {
                        "id": row.id,
                        "order": "1.00000000000000000000",
                        # Only the visible field should be sent
                        f"field_{visible_field.id}": "Visible",
                    },
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_batch_rows_deleted_public_views_receive_restricted_row_deleted_ws_event(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_view_only_showing_one_field = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    public_view_showing_all_fields = data_fixture.create_grid_view(
        user, table=table, public=True, order=1
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_only_showing_one_field, hidden_field, hidden=True
    )
    model = table.get_model()
    row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "Hidden",
        },
    )
    row2 = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "Hidden",
            "order": 2,
        },
    )

    RowHandler().delete_rows(user, table, [row.id, row2.id], model)

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_only_showing_one_field.slug}",
                {
                    "type": "rows_deleted",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row_ids": [1, 2],
                    "rows": [
                        {
                            "id": row.id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                        {
                            "id": row2.id,
                            "order": "2.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                },
                None,
            ),
            call(
                f"view-{public_view_showing_all_fields.slug}",
                {
                    "type": "rows_deleted",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row_ids": [1, 2],
                    "rows": [
                        {
                            "id": row.id,
                            "order": "1.00000000000000000000",
                            f"field_{visible_field.id}": "Visible",
                            # This field is not hidden for this public view
                            # and so should be included
                            f"field_{hidden_field.id}": "Hidden",
                        },
                        {
                            "id": row2.id,
                            "order": "2.00000000000000000000",
                            f"field_{visible_field.id}": "Visible",
                            # This field is not hidden for this public view
                            # and so should be included
                            f"field_{hidden_field.id}": "Hidden",
                        },
                    ],
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_batch_rows_deleted_public_views_receive_row_deleted_only_when_filters_match(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_view_showing_row = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    public_view_hiding_row = data_fixture.create_grid_view(
        user, table=table, public=True, order=1
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_showing_row, hidden_field, hidden=True
    )
    data_fixture.create_grid_view_field_option(
        public_view_hiding_row, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=visible_field, type="equal", value="Visible"
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=hidden_field, type="equal", value="Not Match"
    )

    # Match
    data_fixture.create_view_filter(
        view=public_view_showing_row, field=visible_field, type="equal", value="Visible"
    )
    # Match
    data_fixture.create_view_filter(
        view=public_view_showing_row, field=hidden_field, type="equal", value="Hidden"
    )

    model = table.get_model()
    row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "Hidden",
        },
    )
    row2 = model.objects.create(
        **{
            f"field_{visible_field.id}": "Not Visible",
            f"field_{hidden_field.id}": "Hidden",
            "order": 2,
        },
    )

    RowHandler().delete_rows(user, table, [row.id, row2.id], model)

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_showing_row.slug}",
                {
                    "type": "rows_deleted",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row_ids": [row.id],
                    "rows": [
                        {
                            "id": row.id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        }
                    ],
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_given_row_not_visible_in_public_view_when_updated_to_be_visible_event_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)

    public_view_with_filters_initially_hiding_all_rows = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_with_filters_initially_hiding_all_rows, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_with_filters_initially_hiding_all_rows,
        field=visible_field,
        type="equal",
        value="Visible",
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_with_filters_initially_hiding_all_rows,
        field=hidden_field,
        type="equal",
        value="ValueWhichMatchesFilter",
    )

    model = table.get_model()
    initially_hidden_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichDoesntMatchFilter",
        },
    )

    # Double check the row isn't visible in any views to begin with
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    assert row_checker.get_public_views_where_row_is_visible(initially_hidden_row) == []

    RowHandler().update_row_by_id(
        user,
        table,
        initially_hidden_row.id,
        values={f"field_{hidden_field.id}": "ValueWhichMatchesFilter"},
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_with_filters_initially_hiding_all_rows.slug}",
                {
                    # The row should appear as a created event as for the public view
                    # it effectively has been created as it didn't exist before.
                    "type": "row_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row": {
                        "id": initially_hidden_row.id,
                        "order": "1.00000000000000000000",
                        # Only the visible field should be sent
                        f"field_{visible_field.id}": "Visible",
                    },
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_batch_update_rows_not_visible_in_public_view_to_be_visible_event_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)

    public_view_with_filters_initially_hiding_all_rows = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_with_filters_initially_hiding_all_rows, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_with_filters_initially_hiding_all_rows,
        field=visible_field,
        type="equal",
        value="Visible",
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_with_filters_initially_hiding_all_rows,
        field=hidden_field,
        type="equal",
        value="ValueWhichMatchesFilter",
    )

    model = table.get_model()
    initially_hidden_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichDoesntMatchFilter",
        },
    )
    initially_hidden_row2 = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichDoesntMatchFilter",
            "order": 2,
        },
    )

    # Double check the row isn't visible in any views to begin with
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    assert (
        row_checker.get_public_views_where_rows_are_visible(
            [initially_hidden_row, initially_hidden_row2]
        )
        == []
    )

    with transaction.atomic():
        RowHandler().update_rows(
            user,
            table,
            [
                {
                    "id": initially_hidden_row.id,
                    f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
                },
                {
                    "id": initially_hidden_row2.id,
                    f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
                },
            ],
        )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_with_filters_initially_hiding_all_rows.slug}",
                {
                    # The row should appear as a created event as for the public view
                    # it effectively has been created as it didn't exist before.
                    "type": "rows_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "rows": [
                        {
                            "id": initially_hidden_row.id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                        {
                            "id": initially_hidden_row2.id,
                            "order": "2.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_batch_update_rows_some_not_visible_in_public_view_to_be_visible_event_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)

    public_view_with_filters_initially_hiding_all_rows = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_with_filters_initially_hiding_all_rows, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_with_filters_initially_hiding_all_rows,
        field=visible_field,
        type="equal",
        value="Visible",
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_with_filters_initially_hiding_all_rows,
        field=hidden_field,
        type="equal",
        value="ValueWhichMatchesFilter",
    )

    model = table.get_model()
    initially_hidden_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichDoesntMatchFilter",
        },
    )
    initially_visible_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
            "order": 2,
        },
    )

    # Double check the row isn't visible in any views to begin with
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    assert (
        row_checker.get_public_views_where_rows_are_visible([initially_hidden_row])
        == []
    )

    with transaction.atomic():
        RowHandler().update_rows(
            user,
            table,
            [
                {
                    "id": initially_hidden_row.id,
                    f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
                },
                {
                    "id": initially_visible_row.id,
                    f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
                },
            ],
        )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_with_filters_initially_hiding_all_rows.slug}",
                {
                    "type": "rows_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "rows": [
                        {
                            "id": initially_hidden_row.id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
            call(
                f"view-{public_view_with_filters_initially_hiding_all_rows.slug}",
                {
                    "type": "rows_updated",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "rows_before_update": [
                        {
                            "id": initially_visible_row.id,
                            "order": "2.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                    "rows": [
                        {
                            "id": initially_visible_row.id,
                            "order": "2.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                    "metadata": {},
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_batch_update_rows_visible_in_public_view_to_some_not_be_visible_event_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)

    public_view_with_filters_initially_hiding_all_rows = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_with_filters_initially_hiding_all_rows, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_with_filters_initially_hiding_all_rows,
        field=visible_field,
        type="equal",
        value="Visible",
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_with_filters_initially_hiding_all_rows,
        field=hidden_field,
        type="equal",
        value="ValueWhichMatchesFilter",
    )

    model = table.get_model()
    initially_visible_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
        },
    )
    initially_visible_row2 = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
            "order": 2,
        },
    )

    # Double check the row isn't visible in any views to begin with
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    assert row_checker.get_public_views_where_rows_are_visible(
        [initially_visible_row, initially_visible_row2]
    ) == [
        PublicViewRows(
            ViewHandler().get_view(
                public_view_with_filters_initially_hiding_all_rows.id
            ),
            allowed_row_ids={1, 2},
        )
    ]

    with transaction.atomic():
        RowHandler().update_rows(
            user,
            table,
            [
                {
                    "id": initially_visible_row.id,
                    f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
                },
                {
                    "id": initially_visible_row2.id,
                    f"field_{hidden_field.id}": "ValueWhichDoesntMatchFilter",
                },
            ],
        )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_with_filters_initially_hiding_all_rows.slug}",
                {
                    "type": "rows_deleted",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row_ids": [2],
                    "rows": [
                        {
                            "id": initially_visible_row2.id,
                            "order": "2.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                },
                None,
            ),
            call(
                f"view-{public_view_with_filters_initially_hiding_all_rows.slug}",
                {
                    "type": "rows_updated",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "rows_before_update": [
                        {
                            "id": initially_visible_row.id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                    "rows": [
                        {
                            "id": initially_visible_row.id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                    "metadata": {},
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_given_row_visible_in_public_view_when_updated_to_be_not_visible_event_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)

    public_view_with_row_showing = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_with_row_showing, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_with_row_showing,
        field=visible_field,
        type="contains",
        value="Visible",
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_with_row_showing,
        field=hidden_field,
        type="equal",
        value="ValueWhichMatchesFilter",
    )

    model = table.get_model()
    initially_visible_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
        },
    )

    # Double check the row is visible in the view to start with
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    assert row_checker.get_public_views_where_row_is_visible(initially_visible_row) == [
        public_view_with_row_showing.view_ptr
    ]

    # Update the row so it is no longer visible
    RowHandler().update_row_by_id(
        user,
        table,
        initially_visible_row.id,
        values={
            f"field_{hidden_field.id}": "ValueWhichDoesNotMatchFilter",
            f"field_{visible_field.id}": "StillVisibleButNew",
        },
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_with_row_showing.slug}",
                {
                    # The row should appear as a deleted event as for the public view
                    # it effectively has been.
                    "type": "row_deleted",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row_id": initially_visible_row.id,
                    "row": {
                        "id": initially_visible_row.id,
                        "order": "1.00000000000000000000",
                        # Only the visible field should be sent in its state before it
                        # was updated
                        f"field_{visible_field.id}": "Visible",
                    },
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_batch_update_rows_visible_in_public_view_to_be_not_visible_event_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)

    public_view_with_row_showing = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_with_row_showing, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_with_row_showing,
        field=visible_field,
        type="contains",
        value="Visible",
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_with_row_showing,
        field=hidden_field,
        type="equal",
        value="ValueWhichMatchesFilter",
    )

    model = table.get_model()
    initially_visible_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
        },
    )
    initially_visible_row2 = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
            "order": 2,
        },
    )

    # Double check the row is visible in any views to begin with
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    assert row_checker.get_public_views_where_rows_are_visible(
        [initially_visible_row, initially_visible_row2]
    ) == [
        PublicViewRows(
            ViewHandler().get_view(public_view_with_row_showing.id),
            allowed_row_ids={1, 2},
        )
    ]

    # Update rows so that they are no longer visible
    with transaction.atomic():
        RowHandler().update_rows(
            user,
            table,
            [
                {
                    "id": initially_visible_row.id,
                    f"field_{visible_field.id}": "StillVisibleButNew",
                    f"field_{hidden_field.id}": "ValueWhichDoesNotMatchFilter",
                },
                {
                    "id": initially_visible_row2.id,
                    f"field_{visible_field.id}": "StillVisibleButNew",
                    f"field_{hidden_field.id}": "ValueWhichDoesNotMatchFilter",
                },
            ],
        )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_with_row_showing.slug}",
                {
                    # The row should appear as a deleted event as for the public view
                    # it effectively has been.
                    "type": "rows_deleted",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row_ids": [initially_visible_row.id, initially_visible_row2.id],
                    "rows": [
                        {
                            "id": initially_visible_row.id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent in its state
                            # before it was updated
                            f"field_{visible_field.id}": "Visible",
                        },
                        {
                            "id": initially_visible_row2.id,
                            "order": "2.00000000000000000000",
                            # Only the visible field should be sent in its state
                            # before it was updated
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_given_row_visible_in_public_view_when_updated_to_still_be_visible_event_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)

    public_view_with_row_showing = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_with_row_showing, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_with_row_showing,
        field=visible_field,
        type="contains",
        value="Visible",
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_with_row_showing,
        field=hidden_field,
        type="contains",
        value="e",
    )

    model = table.get_model()
    initially_visible_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "e",
        },
    )

    # Double check the row is visible in the view to start with
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    assert row_checker.get_public_views_where_row_is_visible(initially_visible_row) == [
        public_view_with_row_showing.view_ptr
    ]

    # Update the row so it is still visible but changed
    RowHandler().update_row_by_id(
        user,
        table,
        initially_visible_row.id,
        values={
            f"field_{hidden_field.id}": "eee",
            f"field_{visible_field.id}": "StillVisibleButUpdated",
        },
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_with_row_showing.slug}",
                {
                    "type": "row_updated",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row_before_update": {
                        "id": initially_visible_row.id,
                        "order": "1.00000000000000000000",
                        # Only the visible field should be sent
                        f"field_{visible_field.id}": "Visible",
                    },
                    "row": {
                        "id": initially_visible_row.id,
                        "order": "1.00000000000000000000",
                        # Only the visible field should be sent
                        f"field_{visible_field.id}": "StillVisibleButUpdated",
                    },
                    "metadata": {},
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_batch_update_rows_visible_in_public_view_still_be_visible_event_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)

    public_view_with_row_showing = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_with_row_showing, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_with_row_showing,
        field=visible_field,
        type="contains",
        value="Visible",
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_with_row_showing,
        field=hidden_field,
        type="contains",
        value="e",
    )

    model = table.get_model()
    initially_visible_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "e",
        },
    )
    initially_visible_row2 = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "e",
            "order": 2,
        },
    )

    # Double check the rows are visible in the view to start with
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    assert row_checker.get_public_views_where_rows_are_visible(
        [initially_visible_row, initially_visible_row2]
    ) == [
        PublicViewRows(
            ViewHandler().get_view(public_view_with_row_showing.id),
            allowed_row_ids={1, 2},
        )
    ]

    # Update the row so that they are still visible but changed
    with transaction.atomic():
        RowHandler().update_rows(
            user,
            table,
            [
                {
                    "id": initially_visible_row.id,
                    f"field_{visible_field.id}": "StillVisibleButUpdated",
                    f"field_{hidden_field.id}": "eee",
                },
                {
                    "id": initially_visible_row2.id,
                    f"field_{visible_field.id}": "StillVisibleButUpdated",
                    f"field_{hidden_field.id}": "eee",
                },
            ],
        )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_with_row_showing.slug}",
                {
                    "type": "rows_updated",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "rows_before_update": [
                        {
                            "id": initially_visible_row.id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                        {
                            "id": initially_visible_row2.id,
                            "order": "2.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                    "rows": [
                        {
                            "id": initially_visible_row.id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "StillVisibleButUpdated",
                        },
                        {
                            "id": initially_visible_row2.id,
                            "order": "2.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "StillVisibleButUpdated",
                        },
                    ],
                    "metadata": {},
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_batch_update_subset_rows_visible_in_public_view_no_filters(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)

    public_view_with_row_showing = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )

    model = table.get_model()
    initially_visible_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
        },
    )
    initially_visible_row2 = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            "order": 2,
        },
    )

    # Double check the rows are visible in the view to start with
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    assert row_checker.get_public_views_where_rows_are_visible(
        [initially_visible_row, initially_visible_row2]
    ) == [
        PublicViewRows(
            ViewHandler().get_view(public_view_with_row_showing.id),
            allowed_row_ids=PublicViewRows.ALL_ROWS_ALLOWED,
        )
    ]

    # Update the row so that they are still visible but changed
    with transaction.atomic():
        RowHandler().update_rows(
            user,
            table,
            [
                {
                    "id": initially_visible_row.id,
                    f"field_{visible_field.id}": "StillVisibleButUpdated",
                }
            ],
        )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_with_row_showing.slug}",
                {
                    "type": "rows_updated",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "rows_before_update": [
                        {
                            "id": initially_visible_row.id,
                            "order": "1.00000000000000000000",
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                    "rows": [
                        {
                            "id": initially_visible_row.id,
                            "order": "1.00000000000000000000",
                            f"field_{visible_field.id}": "StillVisibleButUpdated",
                        },
                    ],
                    "metadata": {},
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_row_restored_public_views_receive_restricted_row_created_ws_event(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_view_only_showing_one_field = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    public_view_showing_all_fields = data_fixture.create_grid_view(
        user, table=table, public=True, order=1
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_only_showing_one_field, hidden_field, hidden=True
    )
    model = table.get_model()
    row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "Hidden",
        },
    )
    TrashHandler.trash(
        user, table.database.group, table.database, row, parent_id=table.id
    )
    TrashHandler.restore_item(user, "row", row.id, parent_trash_item_id=table.id)

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_only_showing_one_field.slug}",
                {
                    "type": "row_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row": {
                        "id": row.id,
                        "order": "1.00000000000000000000",
                        # Only the visible field should be sent
                        f"field_{visible_field.id}": "Visible",
                    },
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
            call(
                f"view-{public_view_showing_all_fields.slug}",
                {
                    "type": "row_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row": {
                        "id": row.id,
                        "order": "1.00000000000000000000",
                        f"field_{visible_field.id}": "Visible",
                        # This field is not hidden for this public view and so should be
                        # included
                        f"field_{hidden_field.id}": "Hidden",
                    },
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_row_restored_public_views_receive_row_created_only_when_filters_match(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_view_showing_row = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    public_view_hiding_row = data_fixture.create_grid_view(
        user, table=table, public=True, order=1
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_showing_row, hidden_field, hidden=True
    )
    data_fixture.create_grid_view_field_option(
        public_view_hiding_row, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=visible_field, type="equal", value="Visible"
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=hidden_field, type="equal", value="Not Match"
    )

    # Match
    data_fixture.create_view_filter(
        view=public_view_showing_row, field=visible_field, type="equal", value="Visible"
    )
    # Match
    data_fixture.create_view_filter(
        view=public_view_showing_row, field=hidden_field, type="equal", value="Hidden"
    )

    model = table.get_model()
    row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "Hidden",
        },
    )
    TrashHandler.trash(
        user, table.database.group, table.database, row, parent_id=table.id
    )
    TrashHandler.restore_item(user, "row", row.id, parent_trash_item_id=table.id)

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_showing_row.slug}",
                {
                    "type": "row_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row": {
                        "id": row.id,
                        "order": "1.00000000000000000000",
                        # Only the visible field should be sent
                        f"field_{visible_field.id}": "Visible",
                    },
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_batch_rows_restored_public_views_receive_rows_created_only_when_filters_match(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)
    public_view_showing_row = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    public_view_hiding_row = data_fixture.create_grid_view(
        user, table=table, public=True, order=1
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(
        public_view_showing_row, hidden_field, hidden=True
    )
    data_fixture.create_grid_view_field_option(
        public_view_hiding_row, hidden_field, hidden=True
    )

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=visible_field, type="equal", value="Visible"
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view_hiding_row, field=hidden_field, type="equal", value="Not Match"
    )

    # Match
    data_fixture.create_view_filter(
        view=public_view_showing_row, field=visible_field, type="equal", value="Visible"
    )
    # Match
    data_fixture.create_view_filter(
        view=public_view_showing_row, field=hidden_field, type="equal", value="Hidden"
    )

    model = table.get_model()
    row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "Hidden",
        },
    )
    row2 = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "Hidden",
            "order": 2,
        },
    )

    trashed_rows = TrashedRows()
    trashed_rows.row_ids = [1, 2]
    trashed_rows.table = table
    trashed_rows.rows = [row, row2]

    trash_entry = TrashHandler.trash(
        user, table.database.group, table.database, trashed_rows, parent_id=table.id
    )
    TrashHandler.restore_item(
        user, "rows", trash_entry.trash_item_id, parent_trash_item_id=table.id
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view_showing_row.slug}",
                {
                    "type": "rows_created",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "rows": [
                        {
                            "id": row.id,
                            "order": "1.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                        {
                            "id": row2.id,
                            "order": "2.00000000000000000000",
                            # Only the visible field should be sent
                            f"field_{visible_field.id}": "Visible",
                        },
                    ],
                    "metadata": {},
                    "before_row_id": None,
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_given_row_visible_in_public_view_when_moved_row_updated_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)

    public_view = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(public_view, hidden_field, hidden=True)

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view,
        field=visible_field,
        type="contains",
        value="Visible",
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view,
        field=hidden_field,
        type="equal",
        value="ValueWhichMatchesFilter",
    )

    model = table.get_model()
    visible_moving_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
        },
    )
    invisible_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichDoesNotMatchesFilter",
        },
    )

    # Double check the row is visible in the view to start with
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    assert row_checker.get_public_views_where_row_is_visible(visible_moving_row) == [
        public_view.view_ptr
    ]

    # Move the visible row behind the invisible one
    with transaction.atomic():
        RowHandler().move_row_by_id(
            user, table, visible_moving_row.id, before_row=invisible_row, model=model
        )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view.slug}",
                {
                    # The row should appear as a deleted event as for the public view
                    # it effectively has been.
                    "type": "row_updated",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "row_before_update": {
                        "id": visible_moving_row.id,
                        "order": "1.00000000000000000000",
                        # Only the visible field should be sent
                        f"field_{visible_field.id}": "Visible",
                    },
                    "row": {
                        "id": visible_moving_row.id,
                        "order": "0.99999999999999999999",
                        # Only the visible field should be sent
                        f"field_{visible_field.id}": "Visible",
                    },
                    "metadata": {},
                },
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_given_row_invisible_in_public_view_when_moved_no_update_sent(
    mock_broadcast_to_channel_group, data_fixture
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table)
    hidden_field = data_fixture.create_text_field(table=table)

    public_view = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    data_fixture.create_grid_view_field_option(public_view, hidden_field, hidden=True)

    # Match the visible field
    data_fixture.create_view_filter(
        view=public_view,
        field=visible_field,
        type="contains",
        value="Visible",
    )
    # But filter out based on the hidden field
    data_fixture.create_view_filter(
        view=public_view,
        field=hidden_field,
        type="equal",
        value="ValueWhichMatchesFilter",
    )

    model = table.get_model()
    visible_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichMatchesFilter",
        },
    )
    invisible_moving_row = model.objects.create(
        **{
            f"field_{visible_field.id}": "Visible",
            f"field_{hidden_field.id}": "ValueWhichDoesNotMatchesFilter",
        },
    )

    # Double check the row is visible in the view to start with
    row_checker = ViewHandler().get_public_views_row_checker(
        table, model, only_include_views_which_want_realtime_events=True
    )
    assert row_checker.get_public_views_where_row_is_visible(invisible_moving_row) == []

    # Move the invisible row
    with transaction.atomic():
        RowHandler().move_row_by_id(
            user, table, invisible_moving_row.id, before_row=visible_row, model=model
        )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
        ]
    )

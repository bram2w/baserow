import pytest

from unittest.mock import patch

from baserow.contrib.database.views.handler import ViewHandler


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_view_created(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    view = ViewHandler().create_view(
        user=user, table=table, type_name="grid", name="Grid"
    )

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{table.id}"
    assert args[0][1]["type"] == "view_created"
    assert args[0][1]["view"]["id"] == view.id
    assert "filters" in args[0][1]["view"]
    assert "sortings" in args[0][1]["view"]


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_view_updated(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    view = data_fixture.create_grid_view(user=user)
    ViewHandler().update_view(user=user, view=view, name="View")

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{view.table.id}"
    assert args[0][1]["type"] == "view_updated"
    assert args[0][1]["view_id"] == view.id
    assert args[0][1]["view"]["id"] == view.id
    assert "filters" not in args[0][1]["view"]
    assert "sortings" not in args[0][1]["view"]


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_view_deleted(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    view = data_fixture.create_grid_view(user=user)
    view_id = view.id
    table_id = view.table_id
    ViewHandler().delete_view(user=user, view=view)

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{view.table.id}"
    assert args[0][1]["type"] == "view_deleted"
    assert args[0][1]["view_id"] == view_id
    assert args[0][1]["table_id"] == table_id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_views_reordered(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    view = data_fixture.create_grid_view(user=user)
    ViewHandler().order_views(user=user, table=view.table, order=[view.id])

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{view.table.id}"
    assert args[0][1]["type"] == "views_reordered"
    assert args[0][1]["table_id"] == view.table.id
    assert args[0][1]["order"] == [view.id]


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_view_filter_created(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    view = data_fixture.create_grid_view(user=user, table=table)
    view_filter = ViewHandler().create_filter(
        user=user, view=view, type_name="equal", value="test", field=field
    )

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{table.id}"
    assert args[0][1]["type"] == "view_filter_created"
    assert args[0][1]["view_filter"]["id"] == view_filter.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_view_filter_updated(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    view_filter = data_fixture.create_view_filter(user=user)
    view_filter = ViewHandler().update_filter(
        user=user, view_filter=view_filter, value="test2"
    )

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{view_filter.view.table.id}"
    assert args[0][1]["type"] == "view_filter_updated"
    assert args[0][1]["view_filter_id"] == view_filter.id
    assert args[0][1]["view_filter"]["id"] == view_filter.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_view_filter_deleted(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    view_filter = data_fixture.create_view_filter(user=user)
    view_id = view_filter.view.id
    view_filter_id = view_filter.id
    ViewHandler().delete_filter(user=user, view_filter=view_filter)

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{view_filter.view.table.id}"
    assert args[0][1]["type"] == "view_filter_deleted"
    assert args[0][1]["view_id"] == view_id
    assert args[0][1]["view_filter_id"] == view_filter_id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_view_sort_created(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    view = data_fixture.create_grid_view(user=user, table=table)
    view_sort = ViewHandler().create_sort(
        user=user, view=view, field=field, order="ASC"
    )

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{table.id}"
    assert args[0][1]["type"] == "view_sort_created"
    assert args[0][1]["view_sort"]["id"] == view_sort.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_view_sort_updated(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    view_sort = data_fixture.create_view_sort(user=user)
    view_sort = ViewHandler().update_sort(user=user, view_sort=view_sort, order="DESC")

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{view_sort.view.table.id}"
    assert args[0][1]["type"] == "view_sort_updated"
    assert args[0][1]["view_sort_id"] == view_sort.id
    assert args[0][1]["view_sort"]["id"] == view_sort.id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_view_sort_deleted(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    view_sort = data_fixture.create_view_sort(user=user)
    view_id = view_sort.view.id
    view_sort_id = view_sort.id
    ViewHandler().delete_sort(user=user, view_sort=view_sort)

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{view_sort.view.table.id}"
    assert args[0][1]["type"] == "view_sort_deleted"
    assert args[0][1]["view_id"] == view_id
    assert args[0][1]["view_sort_id"] == view_sort_id


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_grid_view_field_options_updated(mock_broadcast_to_channel_group, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    grid_view = data_fixture.create_grid_view(table=table)

    ViewHandler().update_grid_view_field_options(
        user=user,
        grid_view=grid_view,
        field_options={str(text_field.id): {"width": 150}},
    )

    mock_broadcast_to_channel_group.delay.assert_called_once()
    args = mock_broadcast_to_channel_group.delay.call_args
    assert args[0][0] == f"table-{table.id}"
    assert args[0][1]["type"] == "grid_view_field_options_updated"
    assert args[0][1]["grid_view_id"] == grid_view.id
    assert args[0][1]["grid_view_field_options"][text_field.id]["width"] == 150

import pytest

from baserow.contrib.database.action.scopes import TableActionScopeType
from baserow.contrib.database.views.actions import OrderViewsActionType
from baserow.contrib.database.views.handler import ViewHandler
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_order_views(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user)
    view_1 = data_fixture.create_grid_view(user, table=table)
    view_2 = data_fixture.create_grid_view(user, table=table)

    original_order = [view_1.id, view_2.id]
    new_order = [view_2.id, view_1.id]

    ViewHandler().order_views(user, table, original_order)

    assert ViewHandler().get_views_order(user, table, "collaborative") == original_order

    action_type_registry.get_by_type(OrderViewsActionType).do(user, table, new_order)

    assert ViewHandler().get_views_order(user, table, "collaborative") == new_order

    ActionHandler.undo(user, [TableActionScopeType.value(table.id)], session_id)

    assert ViewHandler().get_views_order(user, table, "collaborative") == original_order


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_order_views(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user)
    view_1 = data_fixture.create_grid_view(user, table=table)
    view_2 = data_fixture.create_grid_view(user, table=table)

    original_order = [view_1.id, view_2.id]
    new_order = [view_2.id, view_1.id]

    ViewHandler().order_views(user, table, original_order)

    assert ViewHandler().get_views_order(user, table, "collaborative") == original_order

    action_type_registry.get_by_type(OrderViewsActionType).do(user, table, new_order)

    assert ViewHandler().get_views_order(user, table, "collaborative") == new_order

    ActionHandler.undo(user, [TableActionScopeType.value(table.id)], session_id)

    assert ViewHandler().get_views_order(user, table, "collaborative") == original_order

    ActionHandler.redo(user, [TableActionScopeType.value(table.id)], session_id)

    assert ViewHandler().get_views_order(user, table, "collaborative") == new_order

import pytest

from baserow.contrib.database.action.scopes import TableActionScopeType
from baserow.contrib.database.views.actions import DeleteViewActionType
from baserow.contrib.database.views.models import View
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_delete_view(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    view = data_fixture.create_grid_view(user)

    action_type_registry.get_by_type(DeleteViewActionType).do(user, view)

    assert View.objects.count() == 0

    ActionHandler.undo(user, [TableActionScopeType.value(view.table_id)], session_id)

    assert View.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_delete_view(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    view = data_fixture.create_grid_view(user)

    action_type_registry.get_by_type(DeleteViewActionType).do(user, view)
    ActionHandler.undo(user, [TableActionScopeType.value(view.table_id)], session_id)

    assert View.objects.count() == 1

    ActionHandler.redo(user, [TableActionScopeType.value(view.table_id)], session_id)

    assert View.objects.count() == 0

import pytest

from baserow.contrib.database.action.scopes import TableActionScopeType
from baserow.contrib.database.fields.actions import DeleteFieldActionType
from baserow.contrib.database.fields.models import Field
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_delete_field(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    field = data_fixture.create_number_field(user=user)
    table = field.table

    action_type_registry.get_by_type(DeleteFieldActionType).do(
        user,
        field,
    )

    assert Field.objects.filter(table=table).count() == 0

    action_undone = ActionHandler.undo(
        user, [TableActionScopeType.value(int(table.id))], session_id
    )

    assert_undo_redo_actions_are_valid(action_undone, [DeleteFieldActionType])

    assert Field.objects.filter(table=table).count() == 1


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_delete_field(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    field = data_fixture.create_number_field(user=user)
    table = field.table

    action_type_registry.get_by_type(DeleteFieldActionType).do(
        user,
        field,
    )

    assert Field.objects.filter(table=table).count() == 0

    ActionHandler.undo(user, [TableActionScopeType.value(int(table.id))], session_id)
    action_redone = ActionHandler.redo(
        user, [TableActionScopeType.value(int(table.id))], session_id
    )

    assert_undo_redo_actions_are_valid(action_redone, [DeleteFieldActionType])

    assert Field.objects.filter(table=table).count() == 0

import pytest

from baserow.contrib.database.action.scopes import TableActionScopeType
from baserow.contrib.database.fields.actions import CreateFieldTypeAction
from baserow.contrib.database.fields.models import Field
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry


@pytest.mark.django_db
def test_can_undo_create_field(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user)

    action_type_registry.get_by_type(CreateFieldTypeAction).do(
        user,
        table,
        "number",
        name="some field",
    )

    assert Field.objects.filter(table=table).count() == 1

    action_undone = ActionHandler.undo(
        user, [TableActionScopeType.value(int(table.id))], session_id
    )

    assert action_undone is not None
    assert action_undone.type == CreateFieldTypeAction.type
    assert action_undone.error is None

    assert Field.objects.filter(table=table).count() == 0


@pytest.mark.django_db
def test_can_undo_redo_create_field(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user)

    action_type_registry.get_by_type(CreateFieldTypeAction).do(
        user,
        table,
        "number",
        name="some field",
    )

    assert Field.objects.filter(table=table).count() == 1

    ActionHandler.undo(user, [TableActionScopeType.value(int(table.id))], session_id)
    action_redone = ActionHandler.redo(
        user, [TableActionScopeType.value(int(table.id))], session_id
    )

    assert action_redone is not None
    assert action_redone.type == CreateFieldTypeAction.type
    assert action_redone.error is None

    assert Field.objects.filter(table=table).count() == 1

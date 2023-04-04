import pytest
from pytest_unordered import unordered

from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.action.scopes import WorkspaceActionScopeType
from baserow.core.actions import DuplicateApplicationActionType
from baserow.core.models import Application
from baserow.test_utils.helpers import (
    assert_undo_redo_actions_are_valid,
    setup_interesting_test_database,
)


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_duplicate_interesting_database(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    database_name = "My Application"

    database = setup_interesting_test_database(
        data_fixture, user=user, workspace=workspace, name=database_name
    )

    duplicated_database = action_type_registry.get_by_type(
        DuplicateApplicationActionType
    ).do(user, database)

    assert duplicated_database.name.startswith(database_name)
    assert Application.objects.count() == 2
    assert database.table_set.count() == duplicated_database.table_set.count()

    actions_undone = ActionHandler.undo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )
    assert_undo_redo_actions_are_valid(actions_undone, [DuplicateApplicationActionType])
    assert Application.objects.count() == 1
    assert Application.objects.first().name == database_name


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_duplicate_interesting_database(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    database_name = "My Application"

    database = setup_interesting_test_database(
        data_fixture, user=user, workspace=workspace, name=database_name
    )

    duplicated_database = action_type_registry.get_by_type(
        DuplicateApplicationActionType
    ).do(user, database)

    assert duplicated_database.name.startswith(database_name)
    assert Application.objects.count() == 2

    ActionHandler.undo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )

    actions_redone = ActionHandler.redo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )
    assert_undo_redo_actions_are_valid(actions_redone, [DuplicateApplicationActionType])
    assert Application.objects.count() == 2
    assert list(Application.objects.values_list("name", flat=True)) == unordered(
        [database_name, f"{database_name} 2"]
    )

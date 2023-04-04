from typing import cast

import pytest

from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.action.scopes import RootActionScopeType
from baserow.core.actions import (
    CreateWorkspaceActionType,
    LeaveWorkspaceActionType,
    OrderWorkspacesActionType,
    UpdateWorkspaceActionType,
)
from baserow.core.exceptions import WorkspaceUserIsLastAdmin
from baserow.core.handler import CoreHandler, WorkspaceForUpdate
from baserow.core.models import Workspace


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_creating_workspace(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    workspace_user = action_type_registry.get_by_type(CreateWorkspaceActionType).do(
        user, "test"
    )
    workspace = workspace_user.workspace

    ActionHandler.undo(user, [RootActionScopeType.value()], session_id)

    assert Workspace.objects.filter(pk=workspace.id).count() == 0


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_creating_workspace(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    workspace_user = action_type_registry.get_by_type(CreateWorkspaceActionType).do(
        user, "test"
    )
    workspace2_user = action_type_registry.get_by_type(CreateWorkspaceActionType).do(
        user, "test2"
    )
    workspace = workspace_user.workspace
    workspace2 = workspace2_user.workspace

    ActionHandler.undo(user, [RootActionScopeType.value()], session_id)

    assert not Workspace.objects.filter(pk=workspace2.id).exists()
    assert Workspace.objects.filter(pk=workspace.id).exists()

    ActionHandler.redo(user, [RootActionScopeType.value()], session_id)

    assert Workspace.objects.filter(pk=workspace2.id).exists()
    assert Workspace.objects.filter(pk=workspace.id).exists()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_updating_workspace(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    workspace_user = action_type_registry.get_by_type(CreateWorkspaceActionType).do(
        user, "test"
    )

    updated_workspace = action_type_registry.get_by_type(UpdateWorkspaceActionType).do(
        user, cast(WorkspaceForUpdate, workspace_user.workspace), "new name"
    )

    assert updated_workspace.name == "new name"
    ActionHandler.undo(user, [RootActionScopeType.value()], session_id)
    updated_workspace.refresh_from_db()
    assert updated_workspace.name == "test"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_ordering_workspace(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    workspace_user = action_type_registry.get_by_type(CreateWorkspaceActionType).do(
        user, "test"
    )

    workspace2_user = action_type_registry.get_by_type(CreateWorkspaceActionType).do(
        user, "test2"
    )

    action_type_registry.get_by_type(OrderWorkspacesActionType).do(
        user, [workspace_user.workspace.id, workspace2_user.workspace.id]
    )

    order_original = CoreHandler().get_workspaces_order(user)

    assert order_original == [workspace_user.workspace.id, workspace2_user.workspace.id]

    order_new = [workspace2_user.workspace.id, workspace_user.workspace.id]

    action_type_registry.get_by_type(OrderWorkspacesActionType).do(user, order_new)

    order = CoreHandler().get_workspaces_order(user)

    assert order == order_new

    ActionHandler.undo(user, [RootActionScopeType.value()], session_id)

    order = CoreHandler().get_workspaces_order(user)

    assert order == order_original


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_ordering_workspace(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    workspace_user = action_type_registry.get_by_type(CreateWorkspaceActionType).do(
        user, "test"
    )

    workspace2_user = action_type_registry.get_by_type(CreateWorkspaceActionType).do(
        user, "test2"
    )

    action_type_registry.get_by_type(OrderWorkspacesActionType).do(
        user, [workspace_user.workspace.id, workspace2_user.workspace.id]
    )

    order_original = CoreHandler().get_workspaces_order(user)

    assert order_original == [workspace_user.workspace.id, workspace2_user.workspace.id]

    order_new = [workspace2_user.workspace.id, workspace_user.workspace.id]

    action_type_registry.get_by_type(OrderWorkspacesActionType).do(user, order_new)

    order = CoreHandler().get_workspaces_order(user)

    assert order == order_new

    ActionHandler.undo(user, [RootActionScopeType.value()], session_id)

    order = CoreHandler().get_workspaces_order(user)

    assert order == order_original

    ActionHandler.redo(user, [RootActionScopeType.value()], session_id)

    order = CoreHandler().get_workspaces_order(user)

    assert order == order_new


@pytest.mark.django_db
def test_leave_workspace(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)

    with pytest.raises(WorkspaceUserIsLastAdmin):
        action_type_registry.get(LeaveWorkspaceActionType.type).do(user, workspace)

    second_user = data_fixture.create_user(workspace=workspace)
    action_type_registry.get(LeaveWorkspaceActionType.type).do(second_user, workspace)

    assert workspace.users.count() == 1

import pytest
from pytest_unordered import unordered

from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.action.scopes import WorkspaceActionScopeType
from baserow.core.actions import (
    CreateApplicationActionType,
    DeleteApplicationActionType,
    DuplicateApplicationActionType,
    OrderApplicationsActionType,
    UpdateApplicationActionType,
)
from baserow.core.models import Application
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_order_applications(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    application_1 = data_fixture.create_database_application(
        workspace=workspace, order=1
    )
    application_2 = data_fixture.create_database_application(
        workspace=workspace, order=2
    )

    action_type_registry.get_by_type(OrderApplicationsActionType).do(
        user, workspace, [application_2.id, application_1.id]
    )

    def check_queryset():
        return list(
            Application.objects.all().order_by("order").values_list("id", flat=True)
        )

    assert check_queryset() == [application_2.id, application_1.id]

    ActionHandler.undo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )
    assert check_queryset() == [application_1.id, application_2.id]

    ActionHandler.redo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )
    assert check_queryset() == [application_2.id, application_1.id]


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_create_application(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    application_type = "database"
    application_name = "My Application"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, workspace, application_type, name=application_name
    )

    ActionHandler.undo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )

    assert Application.objects.filter(pk=application.id).count() == 0


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_create_application(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    application_type = "database"
    application_name = "My Application"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, workspace, application_type, name=application_name
    )

    ActionHandler.undo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )
    ActionHandler.redo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )

    assert Application.objects.filter(pk=application.id).count() == 1


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_delete_application(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    application_type = "database"
    application_name = "My Application"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, workspace, application_type, name=application_name
    )

    action_type_registry.get_by_type(DeleteApplicationActionType).do(user, application)

    assert Application.objects.filter(pk=application.id).count() == 0

    ActionHandler.undo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )

    assert Application.objects.filter(pk=application.id).count() == 1


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_delete_application(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    application_type = "database"
    application_name = "My Application"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, workspace, application_type, name=application_name
    )

    action_type_registry.get_by_type(DeleteApplicationActionType).do(user, application)

    assert Application.objects.filter(pk=application.id).count() == 0

    ActionHandler.undo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )

    ActionHandler.redo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )

    assert Application.objects.filter(pk=application.id).count() == 0


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_update_application(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    application_type = "database"
    application_name = "My Application"
    application_name_new = "New application name"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, workspace, application_type, name=application_name
    )

    action_type_registry.get_by_type(UpdateApplicationActionType).do(
        user, application, name=application_name_new
    )

    assert Application.objects.get(pk=application.id).name == application_name_new

    ActionHandler.undo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )

    assert Application.objects.get(pk=application.id).name == application_name


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_update_application(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    application_type = "database"
    application_name = "My Application"
    application_name_new = "New application name"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, workspace, application_type, name=application_name
    )

    action_type_registry.get_by_type(UpdateApplicationActionType).do(
        user, application, name=application_name_new
    )

    assert Application.objects.get(pk=application.id).name == application_name_new

    ActionHandler.undo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )

    ActionHandler.redo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )

    assert Application.objects.get(pk=application.id).name == application_name_new


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_duplicate_simple_application(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    application_name = "My Application"

    application = data_fixture.create_database_application(
        user, workspace=workspace, name=application_name
    )

    new_application = action_type_registry.get_by_type(
        DuplicateApplicationActionType
    ).do(user, application)

    assert new_application.name.startswith(application_name)
    assert Application.objects.count() == 2

    actions_undone = ActionHandler.undo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )

    assert_undo_redo_actions_are_valid(actions_undone, [DuplicateApplicationActionType])
    assert Application.objects.count() == 1
    assert Application.objects.first().name == application_name


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_duplicate_simple_application(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    application_name = "My Application"

    application = data_fixture.create_database_application(
        user, workspace=workspace, name=application_name
    )

    new_application = action_type_registry.get_by_type(
        DuplicateApplicationActionType
    ).do(user, application)

    assert new_application.name.startswith(application_name)
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
        [application_name, f"{application_name} 2"]
    )

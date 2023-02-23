import pytest

from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.action.scopes import GroupActionScopeType
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid
from baserow_enterprise.audit_log.models import AuditLogEntry
from baserow_enterprise.role.actions import BatchAssignRoleActionType
from baserow_enterprise.role.handler import NewRoleAssignment, RoleAssignmentHandler
from baserow_enterprise.role.models import Role, RoleAssignment


@pytest.fixture(autouse=True)
def enable_enterprise_and_roles_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_batch_assign_role(data_fixture, enterprise_data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    user2 = data_fixture.create_user()
    user3 = data_fixture.create_user()
    group = data_fixture.create_group(
        user=user,
        members=[user2, user3],
    )
    database = data_fixture.create_database_application(group=group)

    table = data_fixture.create_database_table(database=database, user=user)

    team1 = enterprise_data_fixture.create_team(group=group, members=[])

    builder_role = Role.objects.get(uid="BUILDER")
    editor_role = Role.objects.get(uid="EDITOR")
    viewer_role = Role.objects.get(uid="VIEWER")

    new_role_assignments = [
        NewRoleAssignment(user2, editor_role, group),
        NewRoleAssignment(user2, builder_role, table),
        NewRoleAssignment(user2, viewer_role, database.application_ptr),
        NewRoleAssignment(user3, builder_role, group),
        NewRoleAssignment(user3, viewer_role, database.application_ptr),
        NewRoleAssignment(user3, builder_role, table),
        NewRoleAssignment(team1, viewer_role, group),
        NewRoleAssignment(team1, builder_role, table),
        NewRoleAssignment(team1, builder_role, database.application_ptr),
    ]

    action_type_registry.get_by_type(BatchAssignRoleActionType).do(
        user, new_role_assignments, group
    )

    assert RoleAssignment.objects.count() == 7

    assert AuditLogEntry.objects.count() == 1
    log_entry = AuditLogEntry.objects.first()
    assert log_entry.description.startswith("Multiple roles")

    actions_undone = ActionHandler.undo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    assert_undo_redo_actions_are_valid(actions_undone, [BatchAssignRoleActionType])
    assert RoleAssignment.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_batch_assign_role_description_for_one_item(
    data_fixture, enterprise_data_fixture
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    user2 = data_fixture.create_user()
    user3 = data_fixture.create_user()
    group = data_fixture.create_group(
        user=user,
        members=[user2, user3],
    )

    editor_role = Role.objects.get(uid="EDITOR")

    new_role_assignments = [
        NewRoleAssignment(user2, editor_role, group),
    ]

    action_type_registry.get_by_type(BatchAssignRoleActionType).do(
        user, new_role_assignments, group
    )

    assert AuditLogEntry.objects.count() == 1
    log_entry = AuditLogEntry.objects.first()
    assert log_entry.description.startswith("Role ")


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_redo_batch_assign_role(data_fixture, enterprise_data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    user2 = data_fixture.create_user()
    user3 = data_fixture.create_user()
    group = data_fixture.create_group(
        user=user,
        members=[user2, user3],
    )
    database = data_fixture.create_database_application(group=group)

    table = data_fixture.create_database_table(database=database, user=user)

    team1 = enterprise_data_fixture.create_team(group=group, members=[])

    builder_role = Role.objects.get(uid="BUILDER")
    editor_role = Role.objects.get(uid="EDITOR")
    viewer_role = Role.objects.get(uid="VIEWER")

    RoleAssignmentHandler().assign_role(
        user2, group, builder_role, scope=database.application_ptr
    )
    RoleAssignmentHandler().assign_role(user2, group, editor_role, scope=table)

    new_role_assignments = [
        NewRoleAssignment(user2, editor_role, group),
        NewRoleAssignment(user2, builder_role, table),
        NewRoleAssignment(user2, viewer_role, database.application_ptr),
        NewRoleAssignment(user3, builder_role, group),
        NewRoleAssignment(user3, viewer_role, database.application_ptr),
        NewRoleAssignment(user3, None, table),
        NewRoleAssignment(team1, viewer_role, group),
        NewRoleAssignment(team1, builder_role, table),
        NewRoleAssignment(team1, builder_role, database.application_ptr),
    ]

    action_type_registry.get_by_type(BatchAssignRoleActionType).do(
        user, new_role_assignments, group
    )

    assert RoleAssignment.objects.count() == 6

    actions_undone = ActionHandler.undo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    assert_undo_redo_actions_are_valid(actions_undone, [BatchAssignRoleActionType])
    assert RoleAssignment.objects.count() == 2

    actions_redone = ActionHandler.redo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )
    assert_undo_redo_actions_are_valid(actions_redone, [BatchAssignRoleActionType])

    assert RoleAssignment.objects.count() == 6

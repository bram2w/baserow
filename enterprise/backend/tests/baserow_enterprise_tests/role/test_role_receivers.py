from unittest.mock import patch

from django.contrib.auth import get_user_model

import pytest

from baserow.contrib.database.models import Database
from baserow.contrib.database.table.models import Table
from baserow.core.handler import CoreHandler
from baserow.core.models import WorkspaceUser
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role, RoleAssignment
from baserow_enterprise.teams.models import Team

User = get_user_model()


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.mark.django_db
def test_deletion_cascading_to_role_assignments(data_fixture, enterprise_data_fixture):
    enterprise_data_fixture.enable_enterprise()
    admin = data_fixture.create_user(email="admin@test.net")

    workspace_1 = data_fixture.create_workspace(
        user=admin,
    )

    database_1 = data_fixture.create_database_application(
        workspace=workspace_1, order=1
    )

    table_1_1, _, _ = data_fixture.build_table(
        columns=[("number", "number"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_1,
        order=1,
    )

    role_builder = Role.objects.get(uid="BUILDER")
    role_viewer = Role.objects.get(uid="VIEWER")

    # Delete a user
    builder = data_fixture.create_user(email="builder@test.net", workspace=workspace_1)
    viewer = data_fixture.create_user(email="viewer@test.net", workspace=workspace_1)

    RoleAssignmentHandler().assign_role(
        builder, workspace_1, role=role_viewer, scope=table_1_1
    )
    RoleAssignmentHandler().assign_role(
        viewer, workspace_1, role=role_builder, scope=database_1
    )

    User.objects.filter(email__contains="test.net").delete()

    assert RoleAssignment.objects.count() == 0

    # Delete a workspaceuser
    builder = data_fixture.create_user(email="builder@test.net", workspace=workspace_1)
    viewer = data_fixture.create_user(email="viewer@test.net", workspace=workspace_1)

    RoleAssignmentHandler().assign_role(
        builder, workspace_1, role=role_viewer, scope=table_1_1
    )
    RoleAssignmentHandler().assign_role(
        viewer, workspace_1, role=role_builder, scope=database_1
    )

    WorkspaceUser.objects.filter(user__email__contains="test.net").delete()

    assert RoleAssignment.objects.count() == 0

    # Delete a team
    CoreHandler().add_user_to_workspace(workspace_1, builder)
    team1 = enterprise_data_fixture.create_team(
        workspace=workspace_1, members=[builder]
    )
    team2 = enterprise_data_fixture.create_team(
        workspace=workspace_1, members=[builder]
    )

    RoleAssignmentHandler().assign_role(
        team1, workspace_1, role=role_builder, scope=workspace_1
    )
    RoleAssignmentHandler().assign_role(
        team1, workspace_1, role=role_viewer, scope=table_1_1
    )
    RoleAssignmentHandler().assign_role(
        team2, workspace_1, role=role_builder, scope=database_1
    )

    Team.objects.all().delete()

    assert RoleAssignment.objects.count() == 0

    # Delete a scope
    CoreHandler().add_user_to_workspace(workspace_1, builder)
    database_2 = data_fixture.create_database_application(
        workspace=workspace_1, order=2
    )
    database_3 = data_fixture.create_database_application(
        workspace=workspace_1, order=3
    )
    table_2_1, _, _ = data_fixture.build_table(
        columns=[("number", "number"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_2,
        order=1,
    )
    table_2_2, _, _ = data_fixture.build_table(
        columns=[("number", "number"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_2,
        order=2,
    )
    table_3_1, _, _ = data_fixture.build_table(
        columns=[("number", "number"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_3,
        order=1,
    )

    RoleAssignmentHandler().assign_role(
        builder, workspace_1, role=role_viewer, scope=table_2_1
    )
    RoleAssignmentHandler().assign_role(
        builder, workspace_1, role=role_viewer, scope=table_2_2
    )
    RoleAssignmentHandler().assign_role(
        builder, workspace_1, role=role_builder, scope=database_2.application_ptr
    )

    RoleAssignmentHandler().assign_role(
        builder, workspace_1, role=role_builder, scope=table_3_1
    )

    Database.objects.filter(id=database_2.id).delete()
    Table.objects.filter(database=database_3).delete()

    assert RoleAssignment.objects.count() == 0


@pytest.mark.django_db
@patch("baserow_enterprise.role.receivers.permissions_updated")
def test_send_permissions_updated_only_if_permissions_were_updated(
    mock_permissions_updated, data_fixture
):
    user_unrelated = data_fixture.create_user()
    workspace_user = data_fixture.create_user_workspace()
    CoreHandler().add_user_to_workspace(
        workspace_user.workspace, user_unrelated, permissions="ADMIN"
    )

    CoreHandler().force_update_workspace_user(
        workspace_user.user, workspace_user, permissions="ADMIN"
    )

    assert not mock_permissions_updated.send.called

    CoreHandler().force_update_workspace_user(
        workspace_user.user, workspace_user, permissions="MEMBER"
    )

    mock_permissions_updated.send.assert_called_once()

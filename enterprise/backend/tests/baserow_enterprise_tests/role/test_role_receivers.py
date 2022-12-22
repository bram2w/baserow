from django.contrib.auth import get_user_model

import pytest

from baserow.contrib.database.models import Database
from baserow.contrib.database.table.models import Table
from baserow.core.handler import CoreHandler
from baserow.core.models import GroupUser
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

    group_1 = data_fixture.create_group(
        user=admin,
    )

    database_1 = data_fixture.create_database_application(group=group_1, order=1)

    table_1_1, _, _ = data_fixture.build_table(
        columns=[("number", "number"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_1,
        order=1,
    )

    role_builder = Role.objects.get(uid="BUILDER")
    role_viewer = Role.objects.get(uid="VIEWER")

    # Delete a user
    builder = data_fixture.create_user(email="builder@test.net", group=group_1)
    viewer = data_fixture.create_user(email="viewer@test.net", group=group_1)

    RoleAssignmentHandler().assign_role(
        builder, group_1, role=role_viewer, scope=table_1_1
    )
    RoleAssignmentHandler().assign_role(
        viewer, group_1, role=role_builder, scope=database_1
    )

    User.objects.filter(email__contains="test.net").delete()

    assert RoleAssignment.objects.count() == 0

    # Delete a groupuser
    builder = data_fixture.create_user(email="builder@test.net", group=group_1)
    viewer = data_fixture.create_user(email="viewer@test.net", group=group_1)

    RoleAssignmentHandler().assign_role(
        builder, group_1, role=role_viewer, scope=table_1_1
    )
    RoleAssignmentHandler().assign_role(
        viewer, group_1, role=role_builder, scope=database_1
    )

    GroupUser.objects.filter(user__email__contains="test.net").delete()

    assert RoleAssignment.objects.count() == 0

    # Delete a team
    CoreHandler().add_user_to_group(group_1, builder)
    team1 = enterprise_data_fixture.create_team(group=group_1, members=[builder])
    team2 = enterprise_data_fixture.create_team(group=group_1, members=[builder])

    RoleAssignmentHandler().assign_role(
        team1, group_1, role=role_builder, scope=group_1
    )
    RoleAssignmentHandler().assign_role(
        team1, group_1, role=role_viewer, scope=table_1_1
    )
    RoleAssignmentHandler().assign_role(
        team2, group_1, role=role_builder, scope=database_1
    )

    Team.objects.all().delete()

    assert RoleAssignment.objects.count() == 0

    # Delete a scope
    CoreHandler().add_user_to_group(group_1, builder)
    database_2 = data_fixture.create_database_application(group=group_1, order=2)
    database_3 = data_fixture.create_database_application(group=group_1, order=3)
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
        builder, group_1, role=role_viewer, scope=table_2_1
    )
    RoleAssignmentHandler().assign_role(
        builder, group_1, role=role_viewer, scope=table_2_2
    )
    RoleAssignmentHandler().assign_role(
        builder, group_1, role=role_builder, scope=database_2.application_ptr
    )

    RoleAssignmentHandler().assign_role(
        builder, group_1, role=role_builder, scope=table_3_1
    )

    Database.objects.filter(id=database_2.id).delete()
    Table.objects.filter(database=database_3).delete()

    assert RoleAssignment.objects.count() == 0

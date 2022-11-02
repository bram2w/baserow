from unittest.mock import patch

from django.test import override_settings

import pytest

from baserow.core.models import GroupUser
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role, RoleAssignment


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.mark.django_db
@override_settings(
    PERMISSION_MANAGERS=["core", "staff", "member", "basic", "role"],
)
def test_create_role_assignment(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user2])

    table = data_fixture.create_database_table(user=user)

    admin_role = Role.objects.get(uid="ADMIN")
    builder_role = Role.objects.get(uid="BUILDER")

    role_assignment_handler = RoleAssignmentHandler()

    assert len(RoleAssignment.objects.all()) == 0

    # Assign a first role
    role_assignment_handler.assign_role(user2, group, builder_role, scope=table)

    role_assignments = list(RoleAssignment.objects.all())

    assert len(role_assignments) == 1

    assert role_assignments[0].scope == table
    assert role_assignments[0].subject == user2
    assert role_assignments[0].role == builder_role
    assert role_assignments[0].group == group

    # Assign an other role
    role_assignment_handler.assign_role(user2, group, admin_role, scope=group)
    role_assignments = list(RoleAssignment.objects.all())
    group_user = GroupUser.objects.get(group=group, user=user2)

    assert len(role_assignments) == 1
    assert group_user.permissions == admin_role.uid

    # Check that we don't create new RoleAssignment for the same scope/subject/group
    role_assignment_handler.assign_role(user2, group, admin_role, scope=table)

    role_assignments = list(RoleAssignment.objects.all())
    assert len(role_assignments) == 1

    # Can we remove a role
    role_assignment_handler.assign_role(user2, group, None, scope=table)

    role_assignments = list(RoleAssignment.objects.all())
    assert len(role_assignments) == 0


@pytest.mark.django_db
@override_settings(
    FEATURE_FLAGS=["roles"],
    PERMISSION_MANAGERS=["core", "staff", "member", "basic", "role"],
)
def test_get_current_role_assignment(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(user=user, group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    role = Role.objects.get(uid="ADMIN")

    RoleAssignmentHandler().assign_role(user, group, role=role)

    role_assignment = RoleAssignmentHandler().get_current_role_assignment(user, group)

    assert role_assignment is not None
    assert role_assignment.role == role
    assert role_assignment.group == group

    RoleAssignmentHandler().assign_role(user, group, role=role, scope=table)

    role_assignment = RoleAssignmentHandler().get_current_role_assignment(
        user, group, scope=table
    )

    assert role_assignment is not None
    assert role_assignment.role == role
    assert role_assignment.group == group


@pytest.mark.django_db
@override_settings(
    FEATURE_FLAGS=["roles"],
    PERMISSION_MANAGERS=["core", "staff", "member", "basic", "role"],
)
def test_remove_role(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(user=user, group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    role = Role.objects.get(uid="ADMIN")

    RoleAssignmentHandler().assign_role(user, group, role=role)
    RoleAssignmentHandler().assign_role(user, group, role=role, scope=table)

    RoleAssignmentHandler().remove_role(user, group)
    RoleAssignmentHandler().remove_role(user, group, scope=table)

    role_assignment_group = RoleAssignmentHandler().get_current_role_assignment(
        user, group
    )
    role_assignment_table = RoleAssignmentHandler().get_current_role_assignment(
        user, group, scope=table
    )

    assert role_assignment_group.role.uid == "NO_ROLE"
    assert role_assignment_table is None


@pytest.mark.django_db(transaction=True)
@override_settings(
    FEATURE_FLAGS=["roles"],
    PERMISSION_MANAGERS=["core", "staff", "member", "basic", "role"],
)
@patch("baserow.ws.signals.broadcast_to_group")
def test_assign_role(mock_broadcast_to_group, data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(user=user, group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    role = Role.objects.get(uid="ADMIN")

    role_assignment_group = RoleAssignmentHandler().assign_role(user, group, role=role)

    mock_broadcast_to_group.delay.assert_called_once()
    args = mock_broadcast_to_group.delay.call_args
    assert args[0][0] == group.id
    assert args[0][1]["type"] == "group_user_updated"
    group_user = group.groupuser_set.get()
    assert args[0][1]["id"] == group_user.id
    assert args[0][1]["group_id"] == group.id
    assert args[0][1]["group_user"]["user_id"] == group_user.user_id
    assert args[0][1]["group_user"]["permissions"] == role.uid

    role_assignment_table = RoleAssignmentHandler().assign_role(
        user, group, role=role, scope=table
    )

    assert role_assignment_group.role == role
    assert role_assignment_table.role == role

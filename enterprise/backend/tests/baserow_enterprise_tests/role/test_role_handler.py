from django.test import override_settings

import pytest
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role, RoleAssignment


@pytest.mark.django_db
@override_settings(
    FEATURE_FLAGS=["roles"],
    PERMISSION_MANAGERS=["core", "staff", "member", "basic", "role"],
)
def test_create_role_assignment(api_client, data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)

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

    assert len(role_assignments) == 2

    # Check that we don't create new RoleAssignment for the same scope/subject/group
    role_assignment_handler.assign_role(user2, group, admin_role, scope=table)

    role_assignments = list(RoleAssignment.objects.all())
    assert len(role_assignments) == 2

    # Can we remove a role
    role_assignment_handler.assign_role(user2, group, None, scope=table)

    role_assignments = list(RoleAssignment.objects.all())
    assert len(role_assignments) == 1

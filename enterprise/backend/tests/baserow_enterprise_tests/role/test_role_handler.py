from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.db.models import Q

import pytest
from pyinstrument import Profiler

from baserow.contrib.database.object_scopes import DatabaseObjectScopeType
from baserow.core.models import GroupUser
from baserow.core.subjects import UserSubjectType
from baserow_enterprise.exceptions import ScopeNotExist, SubjectNotExist
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role, RoleAssignment


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.mark.django_db
def test_create_role_assignment(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user2])
    database = data_fixture.create_database_application(group=group)

    table = data_fixture.create_database_table(user=user, database=database)

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

    # Check that we don't create new RoleAssignment for the same scope/subject/group
    role_assignment_handler.assign_role(user2, group, admin_role, scope=table)

    role_assignments = list(RoleAssignment.objects.all())
    assert len(role_assignments) == 1

    # Assign an other role
    role_assignment_handler.assign_role(user2, group, admin_role, scope=group)
    role_assignments = list(RoleAssignment.objects.all())
    group_user = GroupUser.objects.get(group=group, user=user2)

    assert len(role_assignments) == 1
    assert group_user.permissions == admin_role.uid

    # Can we remove a role
    role_assignment_handler.assign_role(user2, group, None, scope=table)

    role_assignments = list(RoleAssignment.objects.all())
    assert len(role_assignments) == 0


@pytest.mark.django_db
def test_create_role_assignment_unique_constraint(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    role = Role.objects.get(uid="ADMIN")

    RoleAssignment.objects.create(
        subject_id=user.id,
        subject_type=UserSubjectType().get_content_type(),
        role=role,
        group=group,
        scope_id=database.id,
        scope_type=DatabaseObjectScopeType().get_content_type(),
    )

    with pytest.raises(IntegrityError):
        RoleAssignment.objects.create(
            subject_id=user.id,
            subject_type=UserSubjectType().get_content_type(),
            role=role,
            group=group,
            scope_id=database.id,
            scope_type=DatabaseObjectScopeType().get_content_type(),
        )


@pytest.mark.django_db
def test_get_current_role_assignment(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(user=user, group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    role = Role.objects.get(uid="BUILDER")

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
def test_remove_role(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(user=user, group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    role = Role.objects.get(uid="BUILDER")

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

    assert role_assignment_group.role.uid == "NO_ACCESS"
    assert role_assignment_table is None


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.signals.broadcast_to_group")
def test_assign_role(mock_broadcast_to_group, data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(members=[user])
    database = data_fixture.create_database_application(user=user, group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    role = Role.objects.get(uid="BUILDER")

    role_assignment_group = RoleAssignmentHandler().assign_role(user, group, role=role)

    mock_broadcast_to_group.delay.assert_called_once()
    args = mock_broadcast_to_group.delay.call_args
    assert args[0][0] == group.id
    assert args[0][1]["type"] == "group_user_updated"
    group_user = group.groupuser_set.get()
    assert args[0][1]["id"] == group_user.id
    assert args[0][1]["group_id"] == group.id
    assert args[0][1]["group_user"]["user_id"] == group_user.user_id
    assert args[0][1]["group_user"]["permissions"] == "MEMBER"

    role_assignment_table = RoleAssignmentHandler().assign_role(
        user, group, role=role, scope=table
    )

    assert role_assignment_group.role == role
    assert role_assignment_table.role == role


@pytest.mark.django_db
def test_assign_role_unrelated_group(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    group_unrelated = data_fixture.create_group(user=user, members=[user_2])
    database = data_fixture.create_database_application(group=group, user=user)

    admin_role = Role.objects.get(uid="ADMIN")

    with pytest.raises(ScopeNotExist):
        RoleAssignmentHandler().assign_role(user, group_unrelated, admin_role, database)


@pytest.mark.django_db
def test_assign_role_subject_not_in_group(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group, user=user)

    admin_role = Role.objects.get(uid="ADMIN")

    with pytest.raises(SubjectNotExist):
        RoleAssignmentHandler().assign_role(user_2, group, admin_role, database)


@pytest.mark.django_db()
def test_get_role_assignments(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    database = data_fixture.create_database_application(group=group)

    builder_role = Role.objects.get(uid="BUILDER")

    RoleAssignmentHandler().assign_role(user_2, group, role=builder_role, scope=group)

    group_level_role_assignments = RoleAssignmentHandler().get_role_assignments(
        group, scope=group
    )
    database_level_role_assignments = RoleAssignmentHandler().get_role_assignments(
        group, scope=database
    )

    assert len(group_level_role_assignments) == 2
    assert len(database_level_role_assignments) == 0

    RoleAssignmentHandler().assign_role(
        user_2, group, role=builder_role, scope=database
    )

    group_level_role_assignments = RoleAssignmentHandler().get_role_assignments(
        group, scope=group
    )
    database_level_role_assignments = RoleAssignmentHandler().get_role_assignments(
        group, scope=database
    )

    assert len(group_level_role_assignments) == 2
    assert len(database_level_role_assignments) == 1


@pytest.mark.django_db()
def test_get_role_assignments_invalid_group_and_scope_combination(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    group_2 = data_fixture.create_group(user=user_2)
    database = data_fixture.create_database_application(group=group)

    admin_role = Role.objects.get(uid="ADMIN")

    RoleAssignmentHandler().assign_role(user_2, group, role=admin_role, scope=database)

    role_assignments = RoleAssignmentHandler().get_role_assignments(
        group_2, scope=database
    )

    assert len(role_assignments) == 0


@pytest.mark.django_db
def test_assign_role_batch_group_level(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])

    user_type = ContentType.objects.get_for_model(user)
    group_type = ContentType.objects.get_for_model(group)
    admin_role = Role.objects.get(uid="ADMIN")

    values = [
        {
            "subject": user_2,
            "subject_id": user_2.id,
            "subject_type": user_type,
            "role": admin_role,
            "scope": group,
            "scope_id": group.id,
            "scope_type": group_type,
        }
    ]

    RoleAssignmentHandler().assign_role_batch(user, group, values)

    assert GroupUser.objects.get(user=user_2).permissions == admin_role.uid


@pytest.mark.django_db
def test_assign_role_batch_create_role_assignments(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    database = data_fixture.create_database_application(group=group)

    user_type = ContentType.objects.get_for_model(user)
    database_type = ContentType.objects.get_for_model(database)
    admin_role = Role.objects.get(uid="ADMIN")

    values = [
        {
            "subject": user_2,
            "subject_id": user_2.id,
            "subject_type": user_type,
            "role": admin_role,
            "scope": database,
            "scope_id": database.id,
            "scope_type": database_type,
        }
    ]

    RoleAssignmentHandler().assign_role_batch(user, group, values)

    role_assignments = RoleAssignment.objects.all()

    # Nothing has changed here
    assert GroupUser.objects.get(user=user_2).permissions == "MEMBER"

    assert len(role_assignments) == 1
    assert role_assignments[0].subject == user_2
    assert role_assignments[0].role == admin_role


@pytest.mark.django_db
def test_assign_role_batch_update_role_assignments(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    database = data_fixture.create_database_application(group=group)

    user_type = ContentType.objects.get_for_model(user)
    database_type = ContentType.objects.get_for_model(database)
    admin_role = Role.objects.get(uid="ADMIN")
    builder_role = Role.objects.get(uid="BUILDER")

    RoleAssignmentHandler().assign_role(user_2, group, admin_role, scope=database)

    values = [
        {
            "subject": user_2,
            "subject_id": user_2.id,
            "subject_type": user_type,
            "role": builder_role,
            "scope": database,
            "scope_id": database.id,
            "scope_type": database_type,
        }
    ]

    RoleAssignmentHandler().assign_role_batch(user, group, values)

    role_assignments = RoleAssignment.objects.all()

    # Nothing has changed here
    assert GroupUser.objects.get(user=user_2).permissions == "MEMBER"

    assert len(role_assignments) == 1
    assert role_assignments[0].subject == user_2
    assert role_assignments[0].role == builder_role


@pytest.mark.django_db
def test_assign_role_batch_delete_role_assignments(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    database = data_fixture.create_database_application(group=group)

    user_type = ContentType.objects.get_for_model(user)
    database_type = ContentType.objects.get_for_model(database)
    admin_role = Role.objects.get(uid="ADMIN")

    values = [
        {
            "subject": user_2,
            "subject_id": user_2.id,
            "subject_type": user_type,
            "role": admin_role,
            "scope": database,
            "scope_id": database.id,
            "scope_type": database_type,
        }
    ]

    RoleAssignmentHandler().assign_role_batch(user, group, values)

    role_assignments = RoleAssignment.objects.all()

    assert len(role_assignments) == 1
    assert role_assignments[0].subject == user_2
    assert role_assignments[0].role == admin_role

    values = [
        {
            "subject": user_2,
            "subject_id": user_2.id,
            "subject_type": user_type,
            "role": None,
            "scope": database,
            "scope_id": database.id,
            "scope_type": database_type,
        }
    ]

    RoleAssignmentHandler().assign_role_batch(user, group, values)

    role_assignments = RoleAssignment.objects.all()

    assert len(role_assignments) == 0


@pytest.mark.django_db
def test_assign_role_batch_delete_group_user(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])

    user_type = ContentType.objects.get_for_model(user)
    group_type = ContentType.objects.get_for_model(group)
    admin_role = Role.objects.get(uid="ADMIN")
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    values = [
        {
            "subject": user_2,
            "subject_id": user_2.id,
            "subject_type": user_type,
            "role": admin_role,
            "scope": group,
            "scope_id": group.id,
            "scope_type": group_type,
        }
    ]

    RoleAssignmentHandler().assign_role_batch(user, group, values)

    group_user_2 = GroupUser.objects.get(group=group, user=user_2)
    assert group_user_2.permissions == admin_role.uid

    values = [
        {
            "subject": user_2,
            "subject_id": user_2.id,
            "subject_type": user_type,
            "role": None,
            "scope": group,
            "scope_id": group.id,
            "scope_type": group_type,
        }
    ]

    RoleAssignmentHandler().assign_role_batch(user, group, values)

    group_user_2 = GroupUser.objects.get(group=group, user=user_2)
    assert group_user_2.permissions == no_access_role.uid


@pytest.mark.django_db
def test_assign_role_batch_unrelated_group(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    group_unrelated = data_fixture.create_group(user=user, members=[user_2])
    database = data_fixture.create_database_application(group=group, user=user)

    user_type = ContentType.objects.get_for_model(user)
    database_type = ContentType.objects.get_for_model(database)
    builder_role = Role.objects.get(uid="BUILDER")

    values = [
        {
            "subject": user_2,
            "subject_id": user_2.id,
            "subject_type": user_type,
            "role": builder_role,
            "scope": database,
            "scope_id": database.id,
            "scope_type": database_type,
        }
    ]

    with pytest.raises(ScopeNotExist):
        RoleAssignmentHandler().assign_role_batch(user, group_unrelated, values)


@pytest.mark.django_db
def test_assign_role_batch_subject_not_in_group(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group, user=user)

    user_type = ContentType.objects.get_for_model(user)
    database_type = ContentType.objects.get_for_model(database)
    admin_role = Role.objects.get(uid="ADMIN")

    values = [
        {
            "subject": user_2,
            "subject_id": user_2.id,
            "subject_type": user_type,
            "role": admin_role,
            "scope": database,
            "scope_id": database.id,
            "scope_type": database_type,
        }
    ]

    with pytest.raises(SubjectNotExist):
        RoleAssignmentHandler().assign_role_batch(user, group, values)


@pytest.mark.django_db
@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
# pytest -k "test_assign_role_batch_performance" -s --run-disabled-in-ci
def test_assign_role_batch_performance(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)

    admin_role = Role.objects.get(uid="ADMIN")
    no_access_role = Role.objects.get(uid="NO_ACCESS")
    user_type = ContentType.objects.get_for_model(user)
    group_type = ContentType.objects.get_for_model(group)
    database_type = ContentType.objects.get_for_model(database)

    sample_size = 500

    group_level_updates = []
    for i in range(sample_size):
        user_new = data_fixture.create_user()
        GroupUser.objects.create(
            group=group, user=user_new, order=0, permissions="MEMBER"
        )
        group_level_updates.append(
            {
                "subject": user_new,
                "subject_id": user_new.id,
                "subject_type": user_type,
                "role": admin_role,
                "scope": group,
                "scope_id": group.id,
                "scope_type": group_type,
            }
        )

    profiler = Profiler()
    profiler.start()
    RoleAssignmentHandler().assign_role_batch(user, group, group_level_updates)
    profiler.stop()

    not_initial_user_filter = Q(user__id=user.id)
    group_users = GroupUser.objects.filter(~not_initial_user_filter)
    assert len(group_users) == sample_size

    for group_user in group_users:
        assert group_user.permissions == admin_role.uid

    print("----------GROUP LEVEL UPDATES------------")
    print(profiler.output_text(unicode=True, color=True))

    group_level_deletions = []
    for value in group_level_updates:
        value["role"] = None
        group_level_deletions.append(value)

    profiler = Profiler()
    profiler.start()
    RoleAssignmentHandler().assign_role_batch(user, group, group_level_deletions)
    profiler.stop()

    group_users = GroupUser.objects.filter(~not_initial_user_filter)
    assert len(group_users) == sample_size

    for group_user in group_users:
        assert group_user.permissions == no_access_role.uid

    print("----------GROUP LEVEL DELETIONS------------")
    print(profiler.output_text(unicode=True, color=True))

    database_level_assignments = []
    for value in group_level_updates:
        value["role"] = admin_role
        value["scope"] = database
        value["scope_id"] = database.id
        value["scope_type"] = database_type
        database_level_assignments.append(value)

    profiler = Profiler()
    profiler.start()
    RoleAssignmentHandler().assign_role_batch(user, group, database_level_assignments)
    profiler.stop()

    role_assignments = RoleAssignment.objects.all()
    assert len(role_assignments) == sample_size
    for role_assignment in role_assignments:
        assert role_assignment.scope == database
        assert role_assignment.role == admin_role

    print("----------Database Level Assignments------------")
    print(profiler.output_text(unicode=True, color=True))

    database_level_deletions = []
    for value in database_level_assignments:
        value["role"] = None
        database_level_deletions.append(value)

    profiler = Profiler()
    profiler.start()
    RoleAssignmentHandler().assign_role_batch(user, group, database_level_deletions)
    profiler.stop()

    assert RoleAssignment.objects.count() == 0

    print("----------Database Level Deletions------------")
    print(profiler.output_text(unicode=True, color=True))

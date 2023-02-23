from unittest.mock import patch

from django.db import IntegrityError, connection, reset_queries
from django.db.models import Q
from django.test.utils import CaptureQueriesContext

import pytest
from tqdm import tqdm

from baserow.contrib.database.object_scopes import DatabaseObjectScopeType
from baserow.core.models import GroupUser
from baserow.core.registries import subject_type_registry
from baserow.core.subjects import UserSubjectType
from baserow_enterprise.exceptions import (
    ScopeNotExist,
    SubjectNotExist,
    SubjectUnsupported,
)
from baserow_enterprise.role.constants import ALLOWED_SUBJECT_TYPE_BY_PRIORITY
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role, RoleAssignment
from baserow_enterprise.role.types import NewRoleAssignment


@pytest.fixture(autouse=True)
def enable_enterprise_and_roles_for_all_tests_here(enable_enterprise, synced_roles):
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
    group = data_fixture.create_group(members=[user])
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
def test_get_current_role_assignments(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user(email="user@email.com")
    user1 = data_fixture.create_user(email="user1@email.com")
    user2 = data_fixture.create_user(email="user2@email.com")
    group = data_fixture.create_group(user=user, members=[user1, user2])

    database = data_fixture.create_database_application(user=user, group=group)
    table = data_fixture.create_database_table(user=user, database=database)

    team1 = enterprise_data_fixture.create_team(group=group, members=[user2])

    admin_role = Role.objects.get(uid="ADMIN")
    builder_role = Role.objects.get(uid="BUILDER")
    editor_role = Role.objects.get(uid="EDITOR")
    viewer_role = Role.objects.get(uid="VIEWER")

    RoleAssignmentHandler().assign_role(user, group, role=admin_role)
    RoleAssignmentHandler().assign_role(user1, group, role=builder_role)
    RoleAssignmentHandler().assign_role(user2, group, role=viewer_role)
    RoleAssignmentHandler().assign_role(team1, group, role=editor_role)
    RoleAssignmentHandler().assign_role(
        user, group, role=viewer_role, scope=database.application_ptr
    )
    RoleAssignmentHandler().assign_role(
        user2, group, role=admin_role, scope=database.application_ptr
    )
    RoleAssignmentHandler().assign_role(user, group, role=builder_role, scope=table)
    RoleAssignmentHandler().assign_role(user1, group, role=admin_role, scope=table)
    RoleAssignmentHandler().assign_role(team1, group, role=viewer_role, scope=table)

    for_subject_scope = [
        (user, group),
        (user1, group),
        (user2, group),
        (team1, group),
        (user, database.application_ptr),
        (user1, database.application_ptr),
        (user2, database.application_ptr),
        (team1, database.application_ptr),
        (user, table),
        (user1, table),
        (user2, table),
        (team1, table),
    ]

    role_assignments = RoleAssignmentHandler().get_current_role_assignments(
        group, for_subject_scope
    )

    for (subject, scope), ra in role_assignments.items():
        if ra:
            assert ra.subject == subject
            assert ra.scope == scope

    role_assignment_tuples = [
        (k[0], k[1], v.role.uid if v else None) for k, v in role_assignments.items()
    ]

    assert role_assignment_tuples == [
        (user, group, admin_role.uid),
        (user1, group, builder_role.uid),
        (user2, group, viewer_role.uid),
        (team1, group, editor_role.uid),
        (user, database.application_ptr, viewer_role.uid),
        (user1, database.application_ptr, None),
        (user2, database.application_ptr, admin_role.uid),
        (team1, database.application_ptr, None),
        (user, table, builder_role.uid),
        (user1, table, admin_role.uid),
        (user2, table, None),
        (team1, table, viewer_role.uid),
    ]


@pytest.mark.django_db
def test_remove_role(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(members=[user])
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


@pytest.mark.django_db
def test_get_role_assignments_trashed_teams(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team, user)

    role = Role.objects.get(uid="ADMIN")

    RoleAssignmentHandler().assign_role(team, group, role, scope=database)

    role_assignments = RoleAssignmentHandler().get_role_assignments(
        group, scope=database
    )

    assert len(role_assignments) == 1

    team.trashed = True
    team.save()

    role_assignments = RoleAssignmentHandler().get_role_assignments(
        group, scope=database
    )

    assert len(role_assignments) == 0


@pytest.mark.django_db
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

    admin_role = Role.objects.get(uid="ADMIN")

    values = [
        NewRoleAssignment(
            user_2,
            admin_role,
            group,
        )
    ]

    RoleAssignmentHandler().assign_role_batch_for_user(user, group, values)

    assert GroupUser.objects.get(user=user_2).permissions == admin_role.uid


@pytest.mark.django_db
def test_assign_role_batch_create_role_assignments(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    database = data_fixture.create_database_application(group=group)

    admin_role = Role.objects.get(uid="ADMIN")

    values = [
        NewRoleAssignment(
            user_2,
            admin_role,
            database.application_ptr,
        )
    ]

    RoleAssignmentHandler().assign_role_batch_for_user(user, group, values)

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

    admin_role = Role.objects.get(uid="ADMIN")
    builder_role = Role.objects.get(uid="BUILDER")

    RoleAssignmentHandler().assign_role(
        user_2, group, admin_role, scope=database.application_ptr
    )

    values = [
        NewRoleAssignment(
            user_2,
            builder_role,
            database.application_ptr,
        )
    ]

    RoleAssignmentHandler().assign_role_batch_for_user(user, group, values)

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

    admin_role = Role.objects.get(uid="ADMIN")

    values = [
        NewRoleAssignment(
            user_2,
            admin_role,
            database.application_ptr,
        )
    ]

    RoleAssignmentHandler().assign_role_batch_for_user(user, group, values)

    role_assignments = RoleAssignment.objects.all()

    assert len(role_assignments) == 1
    assert role_assignments[0].subject == user_2
    assert role_assignments[0].role == admin_role

    values = [
        NewRoleAssignment(
            user_2,
            None,
            database.application_ptr,
        )
    ]

    RoleAssignmentHandler().assign_role_batch_for_user(user, group, values)

    role_assignments = RoleAssignment.objects.all()

    assert len(role_assignments) == 0


@pytest.mark.django_db
def test_assign_role_batch_delete_group_user(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])

    admin_role = Role.objects.get(uid="ADMIN")
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    values = [
        NewRoleAssignment(
            user_2,
            admin_role,
            group,
        )
    ]

    RoleAssignmentHandler().assign_role_batch(group, values)

    group_user_2 = GroupUser.objects.get(group=group, user=user_2)
    assert group_user_2.permissions == admin_role.uid

    values = [
        NewRoleAssignment(
            user_2,
            None,
            group,
        )
    ]

    RoleAssignmentHandler().assign_role_batch_for_user(user, group, values)

    group_user_2 = GroupUser.objects.get(group=group, user=user_2)
    assert group_user_2.permissions == no_access_role.uid


@pytest.mark.django_db
def test_assign_role_batch_unrelated_group(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    group_unrelated = data_fixture.create_group(user=user, members=[user_2])
    database = data_fixture.create_database_application(group=group, user=user)

    builder_role = Role.objects.get(uid="BUILDER")

    values = [
        NewRoleAssignment(
            user_2,
            builder_role,
            database.application_ptr,
        )
    ]

    with pytest.raises(ScopeNotExist):
        RoleAssignmentHandler().assign_role_batch_for_user(
            user, group_unrelated, values
        )


@pytest.mark.django_db
def test_assign_role_batch_subject_not_in_group(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group, user=user)

    admin_role = Role.objects.get(uid="ADMIN")

    values = [
        NewRoleAssignment(
            user_2,
            admin_role,
            database.application_ptr,
        )
    ]

    with pytest.raises(SubjectNotExist):
        RoleAssignmentHandler().assign_role_batch_for_user(user, group, values)

    for subject_type in subject_type_registry.get_all():
        if subject_type.type not in ALLOWED_SUBJECT_TYPE_BY_PRIORITY:
            # create a fake instance of subject type
            if subject_type.type == "anonymous":
                actor = subject_type.model_class()

            if subject_type.type == "core.token":
                actor = subject_type.model_class(group=group)
                actor.save()

            values = [
                (
                    NewRoleAssignment(
                        actor,
                        admin_role,
                        database.application_ptr,
                    )
                )
            ]

            with pytest.raises(SubjectUnsupported):
                RoleAssignmentHandler().assign_role_batch_for_user(user, group, values)


@pytest.mark.django_db
@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
# pytest -k "test_assign_role_batch_performance" -s --run-disabled-in-ci
def test_assign_role_batch_performance(data_fixture, profiler):
    admin = data_fixture.create_user()
    group = data_fixture.create_group(user=admin)
    database = data_fixture.create_database_application(group=group)

    admin_role = Role.objects.get(uid="ADMIN")
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    sample_size = 500

    group_level_updates = []
    for _ in tqdm(range(sample_size), desc="Users creation"):
        try:
            user_new = data_fixture.create_user()
        except IntegrityError:
            continue
        else:
            GroupUser.objects.create(
                group=group, user=user_new, order=0, permissions="MEMBER"
            )
            group_level_updates.append(
                NewRoleAssignment(
                    user_new,
                    admin_role,
                    group,
                )
            )

    print("----------GROUP LEVEL------------")
    with profiler(html_report_name="enterprise_batch_assign_group_level"):
        RoleAssignmentHandler().assign_role_batch_for_user(
            admin, group, group_level_updates
        )

    not_initial_user_filter = Q(user__id=admin.id)
    group_users = GroupUser.objects.filter(~not_initial_user_filter)
    assert len(group_users) == sample_size

    for group_user in group_users:
        assert group_user.permissions == admin_role.uid

    group_level_deletions = []
    for (user, _, scope) in group_level_updates:
        group_level_deletions.append(
            NewRoleAssignment(
                user,
                None,
                scope,
            )
        )

    print("----------GROUP LEVEL DELETIONS------------")
    with profiler(html_report_name="enterprise_batch_assign_group_level_deletions"):
        RoleAssignmentHandler().assign_role_batch_for_user(
            admin, group, group_level_deletions
        )

    group_users = GroupUser.objects.filter(~not_initial_user_filter)
    assert len(group_users) == sample_size

    for group_user in group_users:
        assert group_user.permissions == no_access_role.uid

    database_level_assignments = []
    for (user, _, _) in group_level_updates:
        database_level_assignments.append(
            NewRoleAssignment(
                user,
                admin_role,
                database.application_ptr,
            )
        )

    print("----------Database Level Assignments------------")
    with profiler(html_report_name="enterprise_batch_assign_database_level"):
        RoleAssignmentHandler().assign_role_batch_for_user(
            admin, group, database_level_assignments
        )

    role_assignments = RoleAssignment.objects.all()
    assert len(role_assignments) == sample_size
    for role_assignment in role_assignments:
        assert role_assignment.scope == database.application_ptr
        assert role_assignment.role == admin_role

    database_level_deletions = []
    for (user, _, scope) in database_level_assignments:
        database_level_deletions.append(
            NewRoleAssignment(
                user,
                None,
                scope,
            )
        )

    print("----------Database Level Deletions------------")
    with profiler(html_report_name="enterprise_batch_assign_database_level_deletions"):
        RoleAssignmentHandler().assign_role_batch_for_user(
            admin, group, database_level_deletions
        )

    assert RoleAssignment.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_get_roles_per_scope(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user2])
    database1 = data_fixture.create_database_application(user=user, group=group)
    table11 = data_fixture.create_database_table(user=user, database=database1)
    table12 = data_fixture.create_database_table(user=user, database=database1)
    database2 = data_fixture.create_database_application(user=user, group=group)
    table21 = data_fixture.create_database_table(user=user, database=database2)
    table22 = data_fixture.create_database_table(user=user, database=database2)

    team1 = enterprise_data_fixture.create_team(group=group, members=[user2])
    team2 = enterprise_data_fixture.create_team(group=group, members=[user2])
    team3 = enterprise_data_fixture.create_team(group=group, members=[user2])

    admin_role = Role.objects.get(uid="ADMIN")
    editor_role = Role.objects.get(uid="EDITOR")
    builder_role = Role.objects.get(uid="BUILDER")
    viewer_role = Role.objects.get(uid="VIEWER")
    no_role_role = Role.objects.get(uid="NO_ACCESS")
    low_priority_role = Role.objects.get(uid="NO_ROLE_LOW_PRIORITY")

    RoleAssignmentHandler().assign_role(user2, group, role=editor_role, scope=group)

    assert RoleAssignmentHandler().get_roles_per_scope(group, user2) == [
        (group, [editor_role])
    ]

    RoleAssignmentHandler().assign_role(user2, group, role=viewer_role, scope=table11)

    assert RoleAssignmentHandler().get_roles_per_scope(group, user2) == [
        (group, [editor_role]),
        (table11, [viewer_role]),
    ]

    RoleAssignmentHandler().assign_role(
        user2, group, role=builder_role, scope=database1
    )

    assert RoleAssignmentHandler().get_roles_per_scope(group, user2) == [
        (group, [editor_role]),
        (database1, [builder_role]),
        (table11, [viewer_role]),
    ]

    RoleAssignmentHandler().assign_role(user2, group, role=editor_role, scope=database2)
    RoleAssignmentHandler().assign_role(user2, group, role=builder_role, scope=table22)

    assert RoleAssignmentHandler().get_roles_per_scope(group, user2) == [
        (group, [editor_role]),
        (database1, [builder_role]),
        (database2, [editor_role]),
        (table11, [viewer_role]),
        (table22, [builder_role]),
    ]

    RoleAssignmentHandler().assign_role(team1, group, role=editor_role, scope=group)
    RoleAssignmentHandler().assign_role(team2, group, role=builder_role, scope=group)
    RoleAssignmentHandler().assign_role(team3, group, role=no_role_role, scope=group)

    RoleAssignmentHandler().assign_role(team1, group, role=editor_role, scope=database1)

    assert RoleAssignmentHandler().get_roles_per_scope(group, user2) == [
        (group, [editor_role]),
        (database1, [builder_role]),
        (database2, [editor_role]),
        (table11, [viewer_role]),
        (table22, [builder_role]),
    ]

    RoleAssignmentHandler().assign_role(
        team2, group, role=builder_role, scope=database1
    )

    assert RoleAssignmentHandler().get_roles_per_scope(group, user2) == [
        (group, [editor_role]),
        (database1, [builder_role]),
        (database2, [editor_role]),
        (table11, [viewer_role]),
        (table22, [builder_role]),
    ]

    RoleAssignmentHandler().assign_role(
        user2, group, role=low_priority_role, scope=group
    )

    assert RoleAssignmentHandler().get_roles_per_scope(group, user2) == [
        (group, [editor_role, builder_role, no_role_role]),
        (database1, [builder_role]),
        (database2, [editor_role]),
        (table11, [viewer_role]),
        (table22, [builder_role]),
    ]

    RoleAssignmentHandler().assign_role(team1, group, role=editor_role, scope=table12)
    RoleAssignmentHandler().assign_role(team2, group, role=builder_role, scope=table12)
    RoleAssignmentHandler().assign_role(team3, group, role=no_role_role, scope=table12)

    assert RoleAssignmentHandler().get_roles_per_scope(group, user2) == [
        (group, [editor_role, builder_role, no_role_role]),
        (database1, [builder_role]),
        (database2, [editor_role]),
        (table11, [viewer_role]),
        (table12, [editor_role, builder_role, no_role_role]),
        (table22, [builder_role]),
    ]


@pytest.mark.django_db
def test_get_role_per_scope_per_actors(data_fixture, enterprise_data_fixture):
    admin = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    user_3 = data_fixture.create_user()
    user_4 = data_fixture.create_user()
    group = data_fixture.create_group(user=admin, members=[user_2, user_3, user_4])
    database1 = data_fixture.create_database_application(user=admin, group=group)
    table11 = data_fixture.create_database_table(user=admin, database=database1)
    table12 = data_fixture.create_database_table(user=admin, database=database1)
    database2 = data_fixture.create_database_application(user=admin, group=group)
    table21 = data_fixture.create_database_table(user=admin, database=database2)
    table22 = data_fixture.create_database_table(user=admin, database=database2)

    team1 = enterprise_data_fixture.create_team(group=group, members=[user_3])
    team2 = enterprise_data_fixture.create_team(group=group, members=[user_4])
    team3 = enterprise_data_fixture.create_team(group=group, members=[user_3, user_4])

    editor_role = Role.objects.get(uid="EDITOR")
    builder_role = Role.objects.get(uid="BUILDER")
    viewer_role = Role.objects.get(uid="VIEWER")
    no_role_role = Role.objects.get(uid="NO_ACCESS")
    low_priority_role = Role.objects.get(uid="NO_ROLE_LOW_PRIORITY")

    RoleAssignmentHandler().assign_role(user_2, group, role=builder_role, scope=group)
    RoleAssignmentHandler().assign_role(user_3, group, role=no_role_role, scope=group)
    RoleAssignmentHandler().assign_role(
        user_4, group, role=low_priority_role, scope=group
    )

    # User 2 assignments
    RoleAssignmentHandler().assign_role(
        user_2, group, role=editor_role, scope=database1
    )
    RoleAssignmentHandler().assign_role(user_2, group, role=no_role_role, scope=table12)
    RoleAssignmentHandler().assign_role(user_2, group, role=viewer_role, scope=table22)

    # User 4 assignments
    RoleAssignmentHandler().assign_role(
        user_4, group, role=no_role_role, scope=database1
    )
    RoleAssignmentHandler().assign_role(user_4, group, role=builder_role, scope=table11)
    RoleAssignmentHandler().assign_role(user_4, group, role=no_role_role, scope=table22)

    # Team assignments
    RoleAssignmentHandler().assign_role(team1, group, role=builder_role, scope=group)
    RoleAssignmentHandler().assign_role(team1, group, role=viewer_role, scope=database2)
    RoleAssignmentHandler().assign_role(team2, group, role=editor_role, scope=group)
    RoleAssignmentHandler().assign_role(team2, group, role=viewer_role, scope=database2)
    RoleAssignmentHandler().assign_role(team3, group, role=builder_role, scope=group)
    RoleAssignmentHandler().assign_role(team3, group, role=viewer_role, scope=database2)

    result = RoleAssignmentHandler().get_roles_per_scope_for_actors(
        group, subject_type_registry.get("auth.User"), [user_2, user_3, user_4]
    )

    assert len(result) == 3
    assert len(result[user_2]) == 4
    assert result[user_2][0] == (group, [builder_role])
    assert result[user_2][1] == (database1, [editor_role])
    assert result[user_2][2] == (table12, [no_role_role])
    assert result[user_2][3] == (table22, [viewer_role])
    assert len(result[user_3]) == 2
    assert len(result[user_4]) == 5


@pytest.mark.django_db
def test_get_roles_per_scope_trashed_teams(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    team = enterprise_data_fixture.create_team(group=group)
    admin_role = Role.objects.get(uid="ADMIN")

    enterprise_data_fixture.create_subject(team, user)
    RoleAssignmentHandler().assign_role(team, group, admin_role, scope=database)

    assert RoleAssignmentHandler().get_roles_per_scope(group, user) == [
        (group, [admin_role]),
        (database, [admin_role]),
    ]

    team.trashed = True
    team.save()

    assert RoleAssignmentHandler().get_roles_per_scope(group, user) == [
        (group, [admin_role]),
    ]


@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
# pytest -k "test_check_get_role_per_scope_performance" -s --run-disabled-in-ci
def test_check_get_role_per_scope_performance(
    data_fixture, enterprise_data_fixture, profiler
):
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user2])
    database1 = data_fixture.create_database_application(user=user, group=group)
    table11 = data_fixture.create_database_table(user=user, database=database1)
    table12 = data_fixture.create_database_table(user=user, database=database1)
    database2 = data_fixture.create_database_application(user=user, group=group)
    table21 = data_fixture.create_database_table(user=user, database=database2)
    table22 = data_fixture.create_database_table(user=user, database=database2)

    team1 = enterprise_data_fixture.create_team(group=group, members=[user, user2])
    team2 = enterprise_data_fixture.create_team(group=group, members=[user, user2])
    team3 = enterprise_data_fixture.create_team(group=group, members=[user, user2])

    editor_role = Role.objects.get(uid="EDITOR")
    builder_role = Role.objects.get(uid="BUILDER")
    viewer_role = Role.objects.get(uid="VIEWER")
    no_role_role = Role.objects.get(uid="NO_ACCESS")
    low_priority_role = Role.objects.get(uid="NO_ROLE_LOW_PRIORITY")

    RoleAssignmentHandler().assign_role(
        user, group, role=low_priority_role, scope=group
    )
    RoleAssignmentHandler().assign_role(user, group, role=editor_role, scope=database1)
    RoleAssignmentHandler().assign_role(user, group, role=no_role_role, scope=table12)
    RoleAssignmentHandler().assign_role(user, group, role=viewer_role, scope=table22)

    RoleAssignmentHandler().assign_role(team1, group, role=builder_role, scope=group)
    RoleAssignmentHandler().assign_role(team1, group, role=viewer_role, scope=database2)
    RoleAssignmentHandler().assign_role(team2, group, role=editor_role, scope=group)
    RoleAssignmentHandler().assign_role(team2, group, role=viewer_role, scope=database2)
    RoleAssignmentHandler().assign_role(team3, group, role=builder_role, scope=group)
    RoleAssignmentHandler().assign_role(team3, group, role=viewer_role, scope=database2)

    role_assignment_handler = RoleAssignmentHandler()

    with CaptureQueriesContext(connection) as captured:
        role_assignment_handler.get_roles_per_scope(group, user)

    for q in captured.captured_queries:
        print(q)
    print(len(captured.captured_queries))

    with CaptureQueriesContext(connection) as captured:
        role_assignment_handler.get_roles_per_scope(group, user)

    print("----------- Second time ---------------")
    for q in captured.captured_queries:
        print(q)
    print(len(captured.captured_queries))

    with profiler(html_report_name="enterprise_get_roles_per_scope"):
        for i in range(1000):
            role_assignment_handler.get_roles_per_scope(group, user)


@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
# pytest -k "test_get_role_per_scope_for_actors_perf" -s --run-disabled-in-ci
def test_get_role_per_scope_for_actors_perf(
    data_fixture, enterprise_data_fixture, profiler
):
    admin = data_fixture.create_user()

    users = []
    print("Populating database...")

    for _ in tqdm(range(100), desc="Users creation"):
        users.append(data_fixture.create_user())

    group = data_fixture.create_group(user=admin, members=users)

    data = {}
    for _ in tqdm(range(10), desc="Database"):
        database = data_fixture.create_database_application(user=admin, group=group)
        data[database] = []
        for _ in range(10):
            data[database].append(
                data_fixture.create_database_table(user=admin, database=database)
            )

    teams = []
    for max in range(10):
        teams.append(
            enterprise_data_fixture.create_team(
                group=group, members=users[max * 100 : (max + 1) * 100 - 50]
            )
        )

    editor_role = Role.objects.get(uid="EDITOR")
    builder_role = Role.objects.get(uid="BUILDER")
    viewer_role = Role.objects.get(uid="VIEWER")
    no_role_role = Role.objects.get(uid="NO_ACCESS")
    low_priority_role = Role.objects.get(uid="NO_ROLE_LOW_PRIORITY")

    role_assignment_handler = RoleAssignmentHandler()

    def role_gen():
        while True:
            yield editor_role
            yield None
            yield viewer_role
            yield None
            yield no_role_role
            yield None
            yield builder_role
            yield None

    role_generator = role_gen()

    for user in tqdm(users, "User roles"):
        group_role = next(role_generator)
        if group_role is None:
            group_role = low_priority_role

        role_assignment_handler.assign_role(user, group, role=group_role, scope=group)

        for database, tables in data.items():
            role_assignment_handler.assign_role(
                user, group, role=next(role_generator), scope=database
            )
            for table in tables:
                role_assignment_handler.assign_role(
                    user, group, role=next(role_generator), scope=table
                )

    for team in tqdm(teams, "Team roles"):
        for database, tables in data.items():
            role_assignment_handler.assign_role(
                team, group, role=next(role_generator), scope=database
            )
            for table in tables:
                role_assignment_handler.assign_role(
                    team, group, role=next(role_generator), scope=table
                )

    user_subject_type = subject_type_registry.get("auth.User")

    reset_queries()

    with CaptureQueriesContext(connection) as captured:
        role_assignment_handler.get_roles_per_scope_for_actors(
            group, user_subject_type, users
        )

    for q in captured.captured_queries:
        print(q)
    print(len(captured.captured_queries))

    with CaptureQueriesContext(connection) as captured:
        role_assignment_handler.get_roles_per_scope_for_actors(
            group, user_subject_type, users
        )

    print("----------- Second time ---------------")
    for q in captured.captured_queries:
        print(q)
    print(len(captured.captured_queries))

    with profiler(html_report_name="enterprise_get_roles_per_scope_for_actors"):
        for i in range(100):
            role_assignment_handler.get_roles_per_scope_for_actors(
                group, user_subject_type, users
            )

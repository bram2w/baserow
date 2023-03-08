from django.db import connection
from django.db.migrations.executor import MigrationExecutor

import pytest

from baserow_enterprise.role.constants import NO_ACCESS_ROLE_UID


@pytest.fixture(autouse=True)
def enable_enterprise_and_roles_for_all_tests_here(enable_enterprise, synced_roles):
    pass


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()  # reload.
    executor.migrate(target)
    new_state = executor.loader.project_state(target)
    return new_state


@pytest.mark.django_db
def test_0010_with_no_role_without_no_access(synced_roles):
    # Database contains `NO_ROLE`, but not `NO_ACCESS`.
    migrate_from = [
        ("baserow_enterprise", "0009_roleassignment_subject_and_scope_uniqueness"),
    ]
    migrate_to = [
        ("baserow_enterprise", "0010_rename_no_role_to_no_access"),
    ]

    old_state = migrate(migrate_from)

    Role = old_state.apps.get_model("baserow_enterprise", "Role")
    Role.objects.create(uid="NO_ROLE")

    new_state = migrate(migrate_to)

    Role = new_state.apps.get_model("baserow_enterprise", "Role")

    assert not Role.objects.filter(uid="NO_ROLE").exists()
    assert Role.objects.filter(uid=NO_ACCESS_ROLE_UID).exists()


@pytest.mark.django_db
def test_0010_with_no_role_and_no_access_only_no_access_assignments(synced_roles):
    # Database contains `NO_ROLE` and `NO_ACCESS`, but
    # only `RoleAssignment` pointing to `NO_ACCESS`.
    migrate_from = [
        ("core", "0038_group_storage_usage_updated_at"),
        ("baserow_enterprise", "0009_roleassignment_subject_and_scope_uniqueness"),
    ]
    migrate_to = [
        ("baserow_enterprise", "0010_rename_no_role_to_no_access"),
    ]

    old_state = migrate(migrate_from)

    Group = old_state.apps.get_model("core", "Group")
    Role = old_state.apps.get_model("baserow_enterprise", "Role")
    Team = old_state.apps.get_model("baserow_enterprise", "Team")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    RoleAssignment = old_state.apps.get_model("baserow_enterprise", "RoleAssignment")

    Role.objects.create(uid="NO_ROLE")
    no_access = Role.objects.get(uid=NO_ACCESS_ROLE_UID)

    group = Group.objects.create(name="Group")
    team = Team.objects.create(group=group)

    RoleAssignment.objects.create(
        subject_id=team.id,
        subject_type=ContentType.objects.get_for_model(team),
        role=no_access,
        group=group,
        scope_id=group.id,
        scope_type=ContentType.objects.get_for_model(group),
    )

    new_state = migrate(migrate_to)

    Role = new_state.apps.get_model("baserow_enterprise", "Role")
    RoleAssignment = new_state.apps.get_model("baserow_enterprise", "RoleAssignment")

    no_access = Role.objects.get(uid=NO_ACCESS_ROLE_UID)

    assert not Role.objects.filter(uid="NO_ROLE").exists()
    assert Role.objects.filter(uid=NO_ACCESS_ROLE_UID).exists()
    assert RoleAssignment.objects.count() == 1
    assert RoleAssignment.objects.filter(role=no_access).count() == 1


@pytest.mark.django_db
def test_0010_with_no_role_and_no_access_only_no_role_assignments(synced_roles):
    # Database contains `NO_ROLE` and `NO_ACCESS`, but
    # only `RoleAssignment` pointing to `NO_ROLE`.
    migrate_from = [
        ("core", "0038_group_storage_usage_updated_at"),
        ("baserow_enterprise", "0009_roleassignment_subject_and_scope_uniqueness"),
    ]
    migrate_to = [
        ("baserow_enterprise", "0010_rename_no_role_to_no_access"),
    ]

    old_state = migrate(migrate_from)

    Group = old_state.apps.get_model("core", "Group")
    Role = old_state.apps.get_model("baserow_enterprise", "Role")
    Team = old_state.apps.get_model("baserow_enterprise", "Team")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    RoleAssignment = old_state.apps.get_model("baserow_enterprise", "RoleAssignment")

    no_role = Role.objects.create(uid="NO_ROLE")
    assert Role.objects.filter(uid=NO_ACCESS_ROLE_UID).exists()

    group = Group.objects.create(name="Group")
    team = Team.objects.create(group=group)

    RoleAssignment.objects.create(
        subject_id=team.id,
        subject_type=ContentType.objects.get_for_model(team),
        role=no_role,
        group=group,
        scope_id=group.id,
        scope_type=ContentType.objects.get_for_model(group),
    )

    new_state = migrate(migrate_to)

    Role = new_state.apps.get_model("baserow_enterprise", "Role")
    RoleAssignment = new_state.apps.get_model("baserow_enterprise", "RoleAssignment")

    no_access = Role.objects.get(uid=NO_ACCESS_ROLE_UID)

    assert not Role.objects.filter(uid="NO_ROLE").exists()
    assert Role.objects.filter(uid=NO_ACCESS_ROLE_UID).exists()
    assert RoleAssignment.objects.count() == 1
    assert RoleAssignment.objects.filter(role=no_access).count() == 1


@pytest.mark.django_db
def test_0010_with_no_role_and_no_access_mixed_role_assignments(synced_roles):
    # Database contains `NO_ROLE` and `NO_ACCESS`, but
    # with `RoleAssignment` pointing to `NO_ROLE` and `NO_ACCESS`.
    migrate_from = [
        ("core", "0038_group_storage_usage_updated_at"),
        ("baserow_enterprise", "0009_roleassignment_subject_and_scope_uniqueness"),
    ]
    migrate_to = [
        ("baserow_enterprise", "0010_rename_no_role_to_no_access"),
    ]

    old_state = migrate(migrate_from)

    Group = old_state.apps.get_model("core", "Group")
    Role = old_state.apps.get_model("baserow_enterprise", "Role")
    Team = old_state.apps.get_model("baserow_enterprise", "Team")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    RoleAssignment = old_state.apps.get_model("baserow_enterprise", "RoleAssignment")

    no_role = Role.objects.create(uid="NO_ROLE")
    no_access = Role.objects.get(uid=NO_ACCESS_ROLE_UID)

    group = Group.objects.create(name="Group")
    sales = Team.objects.create(group=group, name="Sales")
    engineering = Team.objects.create(group=group, name="Engineering")

    team_ct = ContentType.objects.get_for_model(Team)
    group_ct = ContentType.objects.get_for_model(Group)

    RoleAssignment.objects.bulk_create(
        [
            RoleAssignment(
                subject_id=sales.id,
                subject_type=team_ct,
                role=no_role,
                group=group,
                scope_id=group.id,
                scope_type=group_ct,
            ),
            RoleAssignment(
                subject_id=engineering.id,
                subject_type=team_ct,
                role=no_access,
                group=group,
                scope_id=group.id,
                scope_type=group_ct,
            ),
        ]
    )

    new_state = migrate(migrate_to)

    Role = new_state.apps.get_model("baserow_enterprise", "Role")
    RoleAssignment = new_state.apps.get_model("baserow_enterprise", "RoleAssignment")

    no_access = Role.objects.get(uid=NO_ACCESS_ROLE_UID)

    assert not Role.objects.filter(uid="NO_ROLE").exists()
    assert Role.objects.filter(uid=NO_ACCESS_ROLE_UID).exists()
    assert RoleAssignment.objects.count() == 2
    assert RoleAssignment.objects.filter(role=no_access).count() == 2


@pytest.mark.django_db
def test_0010_migrates_groupusers(synced_roles):
    # `GroupUser` pointing to `NO_ROLE` are migrated to `NO_ACCESS`.
    migrate_from = [
        ("core", "0042_add_ip_address_to_jobs"),
        ("baserow_enterprise", "0009_roleassignment_subject_and_scope_uniqueness"),
    ]
    migrate_to = [
        ("core", "0042_add_ip_address_to_jobs"),
        ("baserow_enterprise", "0010_rename_no_role_to_no_access"),
    ]

    old_state = migrate(migrate_from)

    User = old_state.apps.get_model("auth", "User")
    Group = old_state.apps.get_model("core", "Group")
    GroupUser = old_state.apps.get_model("core", "GroupUser")

    user = User.objects.create()
    group = Group.objects.create(name="Group")
    GroupUser.objects.create(user=user, group=group, permissions="NO_ROLE", order=0)

    new_state = migrate(migrate_to)

    GroupUser = new_state.apps.get_model("core", "GroupUser")
    assert GroupUser.objects.filter(permissions="NO_ROLE").count() == 0
    assert GroupUser.objects.filter(permissions=NO_ACCESS_ROLE_UID).count() == 1

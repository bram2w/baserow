from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

import pytest


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
def test_delete_all_role_assignments_migration(synced_roles):
    migrate_from = [
        ("baserow_enterprise", "0007_teamsubject_baserow_ent_created_01fb9f_idx"),
        ("database", "0092_alter_token_name"),
        ("core", "0038_group_storage_usage_updated_at"),
    ]
    migrate_to = [
        ("baserow_enterprise", "0008_delete_all_role_assignments"),
    ]

    old_state = migrate(migrate_from)

    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    User = old_state.apps.get_model(settings.AUTH_USER_MODEL, require_ready=False)
    Group = old_state.apps.get_model("core", "Group")
    Database = old_state.apps.get_model("database", "Database")
    RoleAssignment = old_state.apps.get_model("baserow_enterprise", "RoleAssignment")
    Role = old_state.apps.get_model("baserow_enterprise", "Role")

    user = User.objects.create()
    role = Role.objects.get(uid="ADMIN")
    database_content_type = ContentType.objects.get_for_model(Database)
    user_content_type = ContentType.objects.get_for_model(User)
    group = Group(name="group")
    group.trashed = False
    group.save()
    database = Database.objects.create(
        content_type=database_content_type,
        order=1,
        name="test",
        group=group,
        trashed=False,
    )

    RoleAssignment.objects.create(
        subject_id=user.id,
        subject_type=user_content_type,
        role=role,
        group=group,
        scope_id=database.id,
        scope_type=database_content_type,
    )

    RoleAssignment.objects.create(
        subject_id=user.id,
        subject_type=user_content_type,
        role=role,
        group=group,
        scope_id=database.id,
        scope_type=database_content_type,
    )

    # Duplicates are in the database
    assert RoleAssignment.objects.count() == 2

    new_state = migrate(migrate_to)
    RoleAssignment = new_state.apps.get_model("baserow_enterprise", "roleassignment")

    # All the role assignments have been deleted
    assert RoleAssignment.objects.count() == 0

import pytest

# noinspection PyPep8Naming
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from baserow.core.trash.handler import TrashHandler

migrate_from = [("core", "0009_user_profile")]
migrate_to = [("core", "0010_fix_trash_constraint")]


# noinspection PyPep8Naming
@pytest.mark.django_db
def test_migration_doesnt_fail_if_duplicate_entries_present_without_parent_id(
    data_fixture, transactional_db, migrate_to_latest_at_end
):
    migrate(migrate_from)

    user = data_fixture.create_user()
    group_to_delete = data_fixture.create_group(user=user)
    other_group_to_delete = data_fixture.create_group(user=user)
    TrashHandler.trash(user, group_to_delete, None, group_to_delete)
    TrashHandler.trash(user, group_to_delete, None, group_to_delete)
    other_trash_entry = TrashHandler.trash(
        user, other_group_to_delete, None, other_group_to_delete
    )

    new_state = migrate(migrate_to)

    MigrationTrashEntry = new_state.apps.get_model("core", "TrashEntry")

    assert MigrationTrashEntry.objects.count() == 2
    assert MigrationTrashEntry.objects.filter(id=other_trash_entry.id).exists()


# noinspection PyPep8Naming
@pytest.mark.django_db
def test_migration_doesnt_fail_if_duplicate_entries_present_with_parent_id(
    data_fixture, transactional_db, migrate_to_latest_at_end
):
    migrate(migrate_from)

    user = data_fixture.create_user()

    group_to_delete = data_fixture.create_group(user=user)
    other_group_to_delete = data_fixture.create_group(user=user)
    first_duplicate_trash_entry = TrashHandler.trash(
        user, group_to_delete, None, group_to_delete
    )
    second_duplicate_trash_entry = TrashHandler.trash(
        user, group_to_delete, None, group_to_delete
    )
    other_group_trash_entry = TrashHandler.trash(
        user, other_group_to_delete, None, other_group_to_delete
    )

    table, fields, rows = data_fixture.build_table(
        columns=[("text", "text")], rows=["first row", "second_row"], user=user
    )
    first_row_trash_entry = TrashHandler.trash(
        user, table.database.group, table.database, rows[0], parent_id=table.id
    )
    # The existing constraint makes it impossible to insert duplicate rows with a
    # parent id so we can't insert one here as it already works. Instead we just check
    # the migration doesn't accidentally delete them.
    second_row_trash_entry = TrashHandler.trash(
        user, table.database.group, table.database, rows[1], parent_id=table.id
    )

    new_state = migrate(migrate_to)

    MigrationTrashEntry = new_state.apps.get_model("core", "TrashEntry")
    assert MigrationTrashEntry.objects.count() == 4
    assert MigrationTrashEntry.objects.filter(id=other_group_trash_entry.id).exists()
    assert MigrationTrashEntry.objects.filter(id=first_row_trash_entry.id).exists()
    assert MigrationTrashEntry.objects.filter(id=second_row_trash_entry.id).exists()
    assert MigrationTrashEntry.objects.filter(
        id=first_duplicate_trash_entry.id
    ).exists()
    assert not MigrationTrashEntry.objects.filter(
        id=second_duplicate_trash_entry.id
    ).exists()


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()  # reload.
    executor.migrate(target)
    new_state = executor.loader.project_state(target)
    return new_state

# noinspection PyPep8Naming
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


def assert_index_exists(table, index_name):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
    select *
    from pg_indexes
    where tablename = 'database_table_{table.id}' and indexname = '{index_name}';
    """
        )
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][2] == index_name


def assert_index_not_exists(table, index_name):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
    select *
    from pg_indexes
    where tablename = 'database_table_{table.id}' and indexname = '{index_name}';
    """
        )
        results = cursor.fetchall()
        assert len(results) == 0


@pytest.mark.django_db(transaction=True)
def test_forwards_migration(data_fixture, reset_schema_after_module):
    migrate_from = [("database", "0064_add_aggregation_field_options")]
    migrate_to = [("database", "0065_rename_old_generated_table_indexes")]

    migrate(migrate_from)

    with connection.cursor() as cursor:
        user = data_fixture.create_user()
        table_with_django_generated_idx = data_fixture.create_database_table(
            user=user, id=48831
        )
        table_with_migration_52_incorrectly_named_idx = (
            data_fixture.create_database_table(id=45229)
        )
        cursor.execute(
            f"CREATE index database_ta_order_79e325_idx on "
            f"database_table_{table_with_django_generated_idx.id}(id)"
        )
        cursor.execute(
            f"CREATE index database_table_45229_order_id_21c3352c on "
            f"database_table_{table_with_migration_52_incorrectly_named_idx.id}(id)"
        )
        cursor.execute(
            f"CREATE index this_index_should_not_be_changed on "
            f"database_table_{table_with_django_generated_idx.id}(id)"
        )

    assert_index_not_exists(
        table_with_django_generated_idx,
        f"tbl_order_id_{table_with_django_generated_idx.id}_idx",
    )
    assert_index_exists(
        table_with_django_generated_idx, f"database_ta_order_79e325_idx"
    )
    assert_index_exists(
        table_with_django_generated_idx, "this_index_should_not_be_changed"
    )

    assert_index_not_exists(
        table_with_migration_52_incorrectly_named_idx,
        f"tbl_order_id_{table_with_migration_52_incorrectly_named_idx.id}_idx",
    )
    assert_index_exists(
        table_with_migration_52_incorrectly_named_idx,
        f"database_table_45229_order_id_21c3352c",
    )

    migrate(migrate_to)

    # Assert the migration has correctly renamed a new tables index with the default
    # django name to the new one
    assert_index_exists(
        table_with_django_generated_idx,
        f"tbl_order_id_{table_with_django_generated_idx.id}_idx",
    )
    assert_index_not_exists(
        table_with_django_generated_idx, f"database_ta_order_79e325_idx"
    )
    assert_index_exists(
        table_with_django_generated_idx, "this_index_should_not_be_changed"
    )

    # Assert the migration has correctly renamed the old incorrect migration name to
    # the new one
    assert_index_exists(
        table_with_migration_52_incorrectly_named_idx,
        f"tbl_order_id_{table_with_migration_52_incorrectly_named_idx.id}_idx",
    )
    assert_index_not_exists(
        table_with_migration_52_incorrectly_named_idx,
        f"database_table_45229_order_id_21c3352c",
    )


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()  # reload.
    executor.migrate(target)
    new_state = executor.loader.project_state(target)
    return new_state

from django.db import ProgrammingError, connection, transaction
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.dummy.base import DatabaseWrapper as DummyDatabaseWrapper
from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as PostgresqlDatabaseSchemaEditor,
)

import pytest

from baserow.contrib.database.db.schema import (
    PostgresqlLenientDatabaseSchemaEditor,
    lenient_schema_editor,
    safe_django_schema_editor,
)
from baserow.contrib.database.table.models import Table


@pytest.mark.django_db
def test_lenient_schema_editor():
    dummy = DummyDatabaseWrapper({})
    with lenient_schema_editor():
        pass

    assert connection.SchemaEditorClass == PostgresqlDatabaseSchemaEditor

    with lenient_schema_editor() as schema_editor:
        assert isinstance(schema_editor, PostgresqlLenientDatabaseSchemaEditor)
        assert isinstance(schema_editor, BaseDatabaseSchemaEditor)
        assert schema_editor.alter_column_prepare_old_value == ""
        assert schema_editor.alter_column_prepare_new_value == ""
        assert not schema_editor.force_alter_column
        assert connection.SchemaEditorClass != PostgresqlDatabaseSchemaEditor

    assert connection.SchemaEditorClass == PostgresqlDatabaseSchemaEditor

    with lenient_schema_editor(
        "p_in = REGEXP_REPLACE(p_in, '', 'test', 'g');",
        "p_in = REGEXP_REPLACE(p_in, 'test', '', 'g');",
        True,
    ) as schema_editor:
        assert schema_editor.alter_column_prepare_old_value == (
            "p_in = REGEXP_REPLACE(p_in, '', 'test', 'g');"
        )
        assert schema_editor.alter_column_prepare_new_value == (
            "p_in = REGEXP_REPLACE(p_in, 'test', '', 'g');"
        )
        assert schema_editor.force_alter_column


# Test provided as an example of how to trigger the django bug. However disabled from CI
# as it will break the connection!
@pytest.mark.django_db
@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
def test_showing_how_djangos_schema_editor_is_broken(data_fixture):
    cxn = transaction.get_connection()
    starting_savepoints = list(cxn.savepoint_ids)
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    other_table = data_fixture.create_database_table(database=database)

    table = Table.objects.create(database=database, order=0)

    # Setup an existing index which will collide with the one that we will make later
    # to ensure the `schema_editor.create_model` will fail in the deferred sql section.
    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE index {table.get_collision_safe_order_id_idx_name()} on "
            f'"database_table_{other_table.id}"("id", "order")'
        )

    cxn = transaction.get_connection()
    assert cxn.savepoint_ids == starting_savepoints
    # Create the table schema in the database database.
    with pytest.raises(
        ProgrammingError, match='relation "tbl_order_id_2_idx" already exists'
    ):
        with connection.schema_editor() as schema_editor:
            # Django only creates indexes when the model is managed.
            model = table.get_model(managed=True)
            schema_editor.create_model(model)

    # Due to the bug in django.db.backends.base.schema.BaseDatabaseSchemaEditor.__exit__
    # we are still in an atomic block even though we weren't in one before!!
    cxn = transaction.get_connection()
    assert cxn.savepoint_ids[0] == starting_savepoints[0]
    # There is still an inner atomic transaction that has not been rolled back!
    assert len(cxn.savepoint_ids) == 2


@pytest.mark.django_db
def test_safe_schema_editor(data_fixture):
    cxn = transaction.get_connection()
    starting_savepoints = list(cxn.savepoint_ids)
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    other_table = data_fixture.create_database_table(database=database)

    table = Table.objects.create(database=database, order=0)

    # Setup an existing index which will collide with the one that we will make later
    # to ensure the `schema_editor.create_model` will fail in the deferred sql section.
    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE index {table.get_collision_safe_order_id_idx_name()} on "
            f'"database_table_{other_table.id}"("id", "order")'
        )

    cxn = transaction.get_connection()
    assert cxn.savepoint_ids == starting_savepoints
    # Create the table schema in the database database.
    with pytest.raises(
        ProgrammingError, match=f'relation "tbl_order_id_{table.id}_idx" already exists'
    ):
        with safe_django_schema_editor() as schema_editor:
            # Django only creates indexes when the model is managed.
            model = table.get_model(managed=True)
            schema_editor.create_model(model)

    # Assert because we are using the safe schema editor the transaction was rolled back
    # successfully!
    cxn = transaction.get_connection()
    assert cxn.savepoint_ids == starting_savepoints


@pytest.mark.django_db
def test_lenient_schema_editor_is_also_safe(data_fixture):
    cxn = transaction.get_connection()
    starting_savepoints = list(cxn.savepoint_ids)
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    other_table = data_fixture.create_database_table(database=database)

    table = Table.objects.create(database=database, order=0)

    # Setup an existing index which will collide with the one that we will make later
    # to ensure the `schema_editor.create_model` will fail in the deferred sql section.
    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE index {table.get_collision_safe_order_id_idx_name()} on "
            f'"database_table_{other_table.id}"("id", "order")'
        )

    cxn = transaction.get_connection()
    assert cxn.savepoint_ids == starting_savepoints
    # Create the table schema in the database database.
    with pytest.raises(
        ProgrammingError, match=f'relation "tbl_order_id_{table.id}_idx" already exists'
    ):
        with lenient_schema_editor(
            None,
            None,
            False,
        ) as schema_editor:
            # Django only creates indexes when the model is managed.
            model = table.get_model(managed=True)
            schema_editor.create_model(model)

    # Assert because we are using the safe schema editor the transaction was rolled back
    # successfully!
    cxn = transaction.get_connection()
    assert cxn.savepoint_ids == starting_savepoints

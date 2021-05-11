import pytest
from django.db import connection
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.dummy.base import DatabaseWrapper as DummyDatabaseWrapper
from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as PostgresqlDatabaseSchemaEditor,
)

from baserow.contrib.database.db.schema import (
    lenient_schema_editor,
    PostgresqlLenientDatabaseSchemaEditor,
)


@pytest.mark.django_db
def test_lenient_schema_editor():
    dummy = DummyDatabaseWrapper({})
    with pytest.raises(ValueError):
        with lenient_schema_editor(dummy):
            pass

    assert connection.SchemaEditorClass == PostgresqlDatabaseSchemaEditor

    with lenient_schema_editor(connection) as schema_editor:
        assert isinstance(schema_editor, PostgresqlLenientDatabaseSchemaEditor)
        assert isinstance(schema_editor, BaseDatabaseSchemaEditor)
        assert schema_editor.alter_column_prepare_old_value == ""
        assert schema_editor.alter_column_prepare_new_value == ""
        assert not schema_editor.force_alter_column
        assert connection.SchemaEditorClass != PostgresqlDatabaseSchemaEditor

    assert connection.SchemaEditorClass == PostgresqlDatabaseSchemaEditor

    with lenient_schema_editor(
        connection,
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

import pytest

from django.db import connection
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.dummy.base import DatabaseWrapper as DummyDatabaseWrapper
from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as PostgresqlDatabaseSchemaEditor
)

from baserow.contrib.database.db.schema import (
    lenient_schema_editor, PostgresqlLenientDatabaseSchemaEditor
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
        assert schema_editor.alert_column_type_function == 'p_in'
        assert connection.SchemaEditorClass != PostgresqlDatabaseSchemaEditor

    assert connection.SchemaEditorClass == PostgresqlDatabaseSchemaEditor

    with lenient_schema_editor(
        connection,
        "REGEXP_REPLACE(p_in, 'test', '', 'g')"
    ) as schema_editor:
        assert schema_editor.alert_column_type_function == \
               "REGEXP_REPLACE(p_in, 'test', '', 'g')"

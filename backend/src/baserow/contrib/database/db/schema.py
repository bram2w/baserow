import contextlib

from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.utils import strip_quotes


class PostgresqlLenientDatabaseSchemaEditor:
    """
    Class changes the behavior of the postgres database schema editor slightly. Normally
    when the field type is altered and one of the data columns doesn't have a value that
    can be casted to the new type, it fails. This class introduces the possibility to
    run a custom function, like REGEXP_REPLACE, to convert the data to the correct
    format. If the casting still fails the value will be set to null.
    """

    sql_alter_column_type = (
        "ALTER COLUMN %(column)s TYPE %(type)s "
        "USING pg_temp.try_cast(%(column)s::text)"
    )
    sql_drop_try_cast = "DROP FUNCTION IF EXISTS pg_temp.try_cast(text, int)"
    sql_create_try_cast = """
        create or replace function pg_temp.try_cast(
            p_in text,
            p_default int default null
        )
            returns %(type)s
        as
        $$
        begin
            begin
                %(alter_column_prepare_old_value)s
                %(alter_column_prepare_new_value)s
                return p_in::%(type)s;
            exception when others then
                return p_default;
            end;
        end;
        $$
        language plpgsql;
    """

    def __init__(
        self,
        *args,
        alter_column_prepare_old_value="",
        alter_column_prepare_new_value="",
        force_alter_column=False,
    ):
        self.alter_column_prepare_old_value = alter_column_prepare_old_value
        self.alter_column_prepare_new_value = alter_column_prepare_new_value
        self.force_alter_column = force_alter_column
        super().__init__(*args)

    def _alter_field(
        self,
        model,
        old_field,
        new_field,
        old_type,
        new_type,
        old_db_params,
        new_db_params,
        strict=False,
    ):
        if self.force_alter_column:
            old_type = f"{old_type}_forced"

        if old_type != new_type:
            variables = {}
            if isinstance(self.alter_column_prepare_old_value, tuple):
                alter_column_prepare_old_value, v = self.alter_column_prepare_old_value
                variables = {**variables, **v}
            else:
                alter_column_prepare_old_value = self.alter_column_prepare_old_value

            if isinstance(self.alter_column_prepare_new_value, tuple):
                alter_column_prepare_new_value, v = self.alter_column_prepare_new_value
                variables = {**variables, **v}
            else:
                alter_column_prepare_new_value = self.alter_column_prepare_new_value

            quoted_column_name = self.quote_name(new_field.column)
            self.execute(self.sql_drop_try_cast)
            self.execute(
                self.sql_create_try_cast
                % {
                    "column": quoted_column_name,
                    "type": new_type,
                    "alter_column_prepare_old_value": alter_column_prepare_old_value,
                    "alter_column_prepare_new_value": alter_column_prepare_new_value,
                },
                variables,
            )

        return super()._alter_field(
            model,
            old_field,
            new_field,
            old_type,
            new_type,
            old_db_params,
            new_db_params,
            strict,
        )

    def _alter_column_type_sql(self, model, old_field, new_field, new_type):
        # Cast when data type changed.
        # Make ALTER TYPE with SERIAL make sense.
        table = strip_quotes(model._meta.db_table)
        serial_fields_map = {
            "bigserial": "bigint",
            "serial": "integer",
            "smallserial": "smallint",
        }
        if new_type.lower() in serial_fields_map:
            column = strip_quotes(new_field.column)
            sequence_name = "%s_%s_seq" % (table, column)
            return (
                (
                    self.sql_alter_column_type
                    % {
                        "column": self.quote_name(column),
                        "type": serial_fields_map[new_type.lower()],
                    },
                    [],
                ),
                [
                    (
                        self.sql_delete_sequence
                        % {
                            "sequence": self.quote_name(sequence_name),
                        },
                        [],
                    ),
                    (
                        self.sql_create_sequence
                        % {
                            "sequence": self.quote_name(sequence_name),
                        },
                        [],
                    ),
                    (
                        self.sql_alter_column
                        % {
                            "table": self.quote_name(table),
                            "changes": self.sql_alter_column_default
                            % {
                                "column": self.quote_name(column),
                                "default": "nextval('%s')"
                                % self.quote_name(sequence_name),
                            },
                        },
                        [],
                    ),
                    (
                        self.sql_set_sequence_max
                        % {
                            "table": self.quote_name(table),
                            "column": self.quote_name(column),
                            "sequence": self.quote_name(sequence_name),
                        },
                        [],
                    ),
                    (
                        self.sql_set_sequence_owner
                        % {
                            "table": self.quote_name(table),
                            "column": self.quote_name(column),
                            "sequence": self.quote_name(sequence_name),
                        },
                        [],
                    ),
                ],
            )
        elif (
            old_field.db_parameters(connection=self.connection)["type"]
            in serial_fields_map
        ):
            # Drop the sequence if migrating away from AutoField.
            column = strip_quotes(new_field.column)
            sequence_name = "%s_%s_seq" % (table, column)
            fragment, _ = BaseDatabaseSchemaEditor._alter_column_type_sql(
                self, model, old_field, new_field, new_type
            )
            return fragment, [
                (
                    self.sql_delete_sequence
                    % {
                        "sequence": self.quote_name(sequence_name),
                    },
                    [],
                ),
            ]
        else:
            return BaseDatabaseSchemaEditor._alter_column_type_sql(
                self, model, old_field, new_field, new_type
            )

    def _field_should_be_altered(self, old_field, new_field):
        return self.force_alter_column or super()._field_should_be_altered(
            old_field, new_field
        )


@contextlib.contextmanager
def lenient_schema_editor(
    connection,
    alter_column_prepare_old_value=None,
    alter_column_prepare_new_value=None,
    force_alter_column=False,
):
    """
    A contextual function that yields a modified version of the connection's schema
    editor. This temporary version is more lenient then the regular editor. Normally
    you can't just alter column types to another type if one the values can't be
    casted to the new type. The lenient schema editor can use a custom SQL function
    to convert the value and if it does not succeed the value will be set to null,
    but it will never fail.

    :param connection: The current connection for which to generate the schema editor
        for.
    :type connection: DatabaseWrapper
    :param alter_column_prepare_old_value: Optionally a query statement converting the
        `p_in` value to a string format.
    :type alter_column_prepare_old_value: None or str
    :param alter_column_prepare_new_value: Optionally a query statement converting the
        `p_in` text value to the new type.
    :type alter_column_prepare_new_value: None or str
    :param force_alter_column: When true forces the schema editor to run an alter
        column statement using the previous two alter_column_prepare parameters.
    :type force_alter_column: bool
    :raises ValueError: When the provided connection is not supported. For now only
        `postgresql` is supported.
    """

    vendor_schema_editor_mapping = {"postgresql": PostgresqlLenientDatabaseSchemaEditor}
    schema_editor_class = vendor_schema_editor_mapping.get(connection.vendor)

    if not schema_editor_class:
        raise ValueError(
            f"The provided connection vendor is not supported. We only "
            f'support {", ".join(vendor_schema_editor_mapping.keys())}.'
        )

    regular_schema_editor = connection.SchemaEditorClass
    schema_editor_class = type(
        "LenientDatabaseSchemaEditor", (schema_editor_class, regular_schema_editor), {}
    )

    connection.SchemaEditorClass = schema_editor_class

    kwargs = {"force_alter_column": force_alter_column}

    if alter_column_prepare_old_value:
        kwargs["alter_column_prepare_old_value"] = alter_column_prepare_old_value

    if alter_column_prepare_new_value:
        kwargs["alter_column_prepare_new_value"] = alter_column_prepare_new_value

    try:
        with connection.schema_editor(**kwargs) as schema_editor:
            yield schema_editor
    except Exception as e:
        raise e
    finally:
        connection.SchemaEditorClass = regular_schema_editor

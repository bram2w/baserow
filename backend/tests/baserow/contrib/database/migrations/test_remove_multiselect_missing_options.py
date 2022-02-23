# noinspection PyPep8Naming
import pytest
from django.core.management import call_command
from django.db import connection, DEFAULT_DB_ALIAS
from django.db.migrations.executor import MigrationExecutor

from baserow.contrib.database.fields.handler import FieldHandler


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()  # reload.
    executor.migrate(target)
    new_state = executor.loader.project_state(target)
    return new_state


# noinspection PyPep8Naming
@pytest.mark.django_db(transaction=True)
def test_forwards_migration(data_fixture, reset_schema_after_module):
    # This particular test wants to do a bunch of setup using actual Baserow code,
    # ensure we have the latest migration applied to the test database so we can run
    # this setup code first. Normally migration tests should first migrate to the
    # schema they care about and then carefully setup state to avoid this problem,
    # however here it is easier to do this.

    call_command("migrate", verbosity=0, database=DEFAULT_DB_ALIAS)
    migrate_from = [("database", "0049_urlfield_2_textfield")]
    migrate_to = [("database", "0050_remove_multiselect_missing_options")]

    field_handler = FieldHandler()

    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field = field_handler.create_field(
        user=user,
        table=table,
        name="Multiple Select",
        type_name="multiple_select",
    )

    option_a = data_fixture.create_select_option(field=field, value="A", color="red")
    option_b = data_fixture.create_select_option(field=field, value="B", color="blue")
    option_c = data_fixture.create_select_option(field=field, value="C", color="green")

    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[option_a.id, option_b.id, option_c.id],
        user=user,
    )

    option_c.delete()

    migrate(migrate_from)

    # We check that we still have a link with the deleted option
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM %(table)s"
            % {
                "table": f"database_multipleselect_{field.id}",
            },
        )
        assert len(cursor.fetchall()) == 3

    migrate(migrate_to)

    # Migration should have only removed relation for deleted option
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM %(table)s"
            % {
                "table": f"database_multipleselect_{field.id}",
            },
        )
        assert len(cursor.fetchall()) == 2

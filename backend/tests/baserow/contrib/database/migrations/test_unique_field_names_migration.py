import pytest

# noinspection PyPep8Naming
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db import DEFAULT_DB_ALIAS
from django.core.management import call_command

migrate_from = [("database", "0032_trash")]
migrate_to = [("database", "0033_unique_field_names")]


# noinspection PyPep8Naming
@pytest.mark.django_db
def test_migration_fixes_duplicate_field_names(data_fixture, transactional_db):
    old_state = migrate(migrate_from)

    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)

    Table = old_state.apps.get_model("database", "Table")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    table = Table.objects.create(database_id=database.id, name="test", order=0)
    other_table = Table.objects.create(database_id=database.id, name="test", order=1)

    TextField = old_state.apps.get_model("database", "TextField")
    Field = old_state.apps.get_model("database", "Field")
    content_type_id = ContentType.objects.get_for_model(TextField).id
    table_1_fields = make_fields_with_names(
        [
            "Duplicate",
            "Duplicate",
        ],
        table.id,
        content_type_id,
        Field,
    )
    table_2_fields = make_fields_with_names(
        [
            "Duplicate",
            "Other",
            "Other",
            "Other",
        ],
        other_table.id,
        content_type_id,
        Field,
    )

    new_state = migrate(migrate_to)

    MigratedField = new_state.apps.get_model("database", "Field")

    assert_fields_name_and_old_name_is(
        [
            ("Duplicate", None),
            ("Duplicate_2", "Duplicate"),
        ],
        table_1_fields,
        MigratedField,
    )

    assert_fields_name_and_old_name_is(
        [
            ("Duplicate", None),
            ("Other", None),
            ("Other_2", "Other"),
            ("Other_3", "Other"),
        ],
        table_2_fields,
        MigratedField,
    )

    # We need to apply the latest migration otherwise other tests might fail.
    call_command("migrate", verbosity=0, database=DEFAULT_DB_ALIAS)


# noinspection PyPep8Naming
@pytest.mark.django_db
def test_migration_handles_existing_fields_with_underscore_number(
    data_fixture, transactional_db
):
    old_state = migrate(migrate_from)
    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)

    Table = old_state.apps.get_model("database", "Table")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    table = Table.objects.create(database_id=database.id, name="test", order=0)

    TextField = old_state.apps.get_model("database", "TextField")
    Field = old_state.apps.get_model("database", "Field")
    content_type_id = ContentType.objects.get_for_model(TextField).id
    table_1_fields = make_fields_with_names(
        [
            "Duplicate",
            "Duplicate",
            "Duplicate",
            "Duplicate_2",
            "Duplicate_2",
            "Duplicate_2",
            "Duplicate_2_2",
            "Duplicate_2_2",
            "Duplicate_3",
            "Duplicate_3",
            "Name Like a Regex [0-9]",
            "Name Like a Regex [0-9]_2",
            "Name Like a Regex [0-9]",
        ],
        table.id,
        content_type_id,
        Field,
    )

    new_state = migrate(migrate_to)
    MigratedField = new_state.apps.get_model("database", "Field")

    assert_fields_name_and_old_name_is(
        [
            ("Duplicate", None),
            ("Duplicate_4", "Duplicate"),
            ("Duplicate_5", "Duplicate"),
            ("Duplicate_2", None),
            ("Duplicate_2_3", "Duplicate_2"),
            ("Duplicate_2_4", "Duplicate_2"),
            ("Duplicate_2_2", None),
            ("Duplicate_2_2_2", "Duplicate_2_2"),
            ("Duplicate_3", None),
            ("Duplicate_3_2", "Duplicate_3"),
            ("Name Like a Regex [0-9]", None),
            ("Name Like a Regex [0-9]_2", None),
            ("Name Like a Regex [0-9]_3", "Name Like a Regex [0-9]"),
        ],
        table_1_fields,
        MigratedField,
    )

    # We need to apply the latest migration otherwise other tests might fail.
    call_command("migrate", verbosity=0, database=DEFAULT_DB_ALIAS)


# noinspection PyPep8Naming
@pytest.mark.django_db
def test_backwards_migration_restores_field_names(data_fixture, transactional_db):

    old_state = migrate(migrate_to)
    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)

    Table = old_state.apps.get_model("database", "Table")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    table = Table.objects.create(database_id=database.id, name="test", order=0)

    TextField = old_state.apps.get_model("database", "TextField")
    Field = old_state.apps.get_model("database", "Field")
    content_type_id = ContentType.objects.get_for_model(TextField).id
    table_1_fields = make_fields_with_names(
        [
            ("Duplicate", None),
            ("Duplicate_2", "Duplicate"),
            ("Duplicate_3", "Duplicate"),
        ],
        table.id,
        content_type_id,
        Field,
    )

    new_state = migrate(migrate_from)
    BackwardsMigratedField = new_state.apps.get_model("database", "Field")

    assert_fields_name_is(
        [
            "Duplicate",
            "Duplicate",
            "Duplicate",
        ],
        table_1_fields,
        BackwardsMigratedField,
    )

    # We need to apply the latest migration otherwise other tests might fail.
    call_command("migrate", verbosity=0, database=DEFAULT_DB_ALIAS)


# noinspection PyPep8Naming
@pytest.mark.django_db
def test_migration_fixes_duplicate_field_names_and_reserved_names(
    data_fixture, transactional_db
):
    old_state = migrate(migrate_from)

    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)

    Table = old_state.apps.get_model("database", "Table")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    table = Table.objects.create(database_id=database.id, name="test", order=0)
    other_table = Table.objects.create(database_id=database.id, name="test", order=1)

    TextField = old_state.apps.get_model("database", "TextField")
    Field = old_state.apps.get_model("database", "Field")
    content_type_id = ContentType.objects.get_for_model(TextField).id

    table_1_fields = make_fields_with_names(
        [
            "Duplicate",
            "Duplicate",
            "id",
            "id",
        ],
        table.id,
        content_type_id,
        Field,
    )
    table_2_fields = make_fields_with_names(
        ["", "order", "order", "Order", "Id"],
        other_table.id,
        content_type_id,
        Field,
    )

    # Run the migration to test
    new_state = migrate(migrate_to)

    # After the initial migration is done, we can use the model state:
    MigratedField = new_state.apps.get_model("database", "Field")

    assert_fields_name_and_old_name_is(
        [
            ("Duplicate", None),
            ("Duplicate_2", "Duplicate"),
            ("id_2", "id"),
            ("id_3", "id"),
        ],
        table_1_fields,
        MigratedField,
    )
    assert_fields_name_and_old_name_is(
        [
            ("Field_1", ""),
            ("order_2", "order"),
            ("order_3", "order"),
            ("Order", None),
            ("Id", None),
        ],
        table_2_fields,
        MigratedField,
    )

    # We need to apply the latest migration otherwise other tests might fail.
    call_command("migrate", verbosity=0, database=DEFAULT_DB_ALIAS)


def make_fields_with_names(field_names, table_id, content_type_id, Field):
    fields = []
    first = True
    for field_name in field_names:
        if isinstance(field_name, tuple):
            field = Field.objects.create(
                name=field_name[0],
                old_name=field_name[1],
                table_id=table_id,
                primary=first,
                order=1,
                content_type_id=content_type_id,
            )
        else:
            field = Field.objects.create(
                name=field_name,
                table_id=table_id,
                primary=first,
                order=1,
                content_type_id=content_type_id,
            )

        fields.append(field)

        first = False
    return fields


# noinspection PyPep8Naming
def assert_fields_name_and_old_name_is(name_old_name_tuples, fields, Field):
    for expected_name, expected_old_name in name_old_name_tuples:
        field = fields.pop(0)

        looked_up_field = Field.objects.get(id=field.id)
        assert looked_up_field.name == expected_name
        if expected_old_name is None:
            assert looked_up_field.old_name is None
        else:
            assert looked_up_field.old_name == expected_old_name


# noinspection PyPep8Naming
def assert_fields_name_is(expected_names, fields, Field):
    for expected_name in expected_names:
        field = fields.pop(0)

        looked_up_field = Field.objects.get(id=field.id)
        assert looked_up_field.name == expected_name


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()  # reload.
    executor.migrate(target)
    new_state = executor.loader.project_state(target)
    return new_state

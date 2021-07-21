from baserow.contrib.database.management.commands.copy_tables import copy_tables


class Struct:
    """
    Test only class to let us go from a dict to an object with the key/values
    as attributes.
    """

    def __init__(self, **entries):
        self.__dict__.update(entries)


def fake_connection(name, tables):
    def table_names():
        return tables

    return Struct(
        **{
            "settings_dict": {
                "NAME": name,
                "HOST": "test_host",
                "PORT": "5432",
                "USER": "test_user",
                "PASSWORD": "test_password",
            },
            "introspection": Struct(
                **{
                    "table_names": table_names,
                }
            ),
        }
    )


def backup_cmd_with_tables(tables):
    return (
        f"pg_dump -h test_host -d source -p 5432 -U test_user -w {tables} | psql -h "
        "test_host -d target -p 5432 -U test_user -w"
    )


def test_a_table_already_in_the_target_db_is_not_in_the_command():
    commands_run = []

    def run_command(command, _):
        commands_run.append(command)

    copy_tables(
        batch_size=10,
        dry_run=False,
        ssl=False,
        source_connection=fake_connection(name="source", tables=["a", "b", "c"]),
        target_connection=fake_connection(name="target", tables=["a"]),
        logger=lambda x: x,
        command_runner=run_command,
    )

    assert commands_run == [backup_cmd_with_tables("-t public.b -t public.c")]


def test_a_batch_size_the_same_as_the_number_of_tables_runs_one_batch():
    commands_run = []

    def run_command(command, env):
        commands_run.append(command)

    tables_to_copy = ["a", "b", "c"]
    copy_tables(
        batch_size=len(tables_to_copy),
        dry_run=False,
        ssl=False,
        source_connection=fake_connection(name="source", tables=tables_to_copy),
        target_connection=fake_connection(name="target", tables=[]),
        logger=lambda x: x,
        command_runner=run_command,
    )

    assert commands_run == [
        backup_cmd_with_tables("-t public.a -t public.b -t public.c")
    ]


def test_a_batch_size_one_more_than_the_number_of_tables_runs_two_batches():
    commands_run = []

    def run_command(command, env):
        commands_run.append(command)

    tables_to_copy = ["a", "b", "c"]
    copy_tables(
        batch_size=len(tables_to_copy) - 1,
        dry_run=False,
        ssl=False,
        source_connection=fake_connection(name="source", tables=tables_to_copy),
        target_connection=fake_connection(name="target", tables=[]),
        logger=lambda x: x,
        command_runner=run_command,
    )

    assert commands_run == [
        backup_cmd_with_tables("-t public.a -t public.b"),
        backup_cmd_with_tables("-t public.c"),
    ]


def test_the_final_batch_includes_all_remaining_tables():
    commands_run = []

    def run_command(command, env):
        commands_run.append(command)

    tables_to_copy = ["a", "b", "c", "d", "e"]
    copy_tables(
        batch_size=2,
        dry_run=False,
        ssl=False,
        source_connection=fake_connection(name="source", tables=tables_to_copy),
        target_connection=fake_connection(name="target", tables=[]),
        logger=lambda x: x,
        command_runner=run_command,
    )

    assert commands_run == [
        backup_cmd_with_tables("-t public.a -t public.b"),
        backup_cmd_with_tables("-t public.c -t public.d"),
        backup_cmd_with_tables("-t public.e"),
    ]


def test_a_batch_with_some_tables_ignored_wont_merge_with_the_next_batch():
    commands_run = []

    def run_command(command, env):
        commands_run.append(command)

    tables_to_copy = ["a", "b", "c"]
    copy_tables(
        batch_size=2,
        dry_run=False,
        ssl=False,
        source_connection=fake_connection(name="source", tables=tables_to_copy),
        target_connection=fake_connection(name="target", tables=["a"]),
        logger=lambda x: x,
        command_runner=run_command,
    )

    assert commands_run == [
        backup_cmd_with_tables("-t public.b"),
        backup_cmd_with_tables("-t public.c"),
    ]

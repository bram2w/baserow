from subprocess import CalledProcessError

from django.core.management.base import BaseCommand, CommandError

from baserow.core.management.backup.backup_runner import (
    BaserowBackupRunner,
    add_shared_postgres_command_args,
)
from baserow.core.management.backup.exceptions import InvalidBaserowBackupArchive


class Command(BaseCommand):
    help = """
        Backs up a Baserow database into a single compressed archive which can be
        restored using the restore_baserow Baserow management command.
        To provide the database password you should either have a valid .pgpass file
        containing the password for the requested connection in the expected postgres
        location (seehttps://www.postgresql.org/docs/current/libpq-pgpass.html) or set
        the PGPASSFILE environment variable.

        WARNING: This command is only safe to run on a database which is not actively
        being updated and not connected to a running version of Baserow for the
        duration of the back-up.

        This command splits the back-up into multiple `pg_dump` runs to export the
        databases tables in batches and so might generate an inconsistent back-up if
        database changes occur partway through the run. Additionally when tables are
        being backed up this command will hold an ACCESS SHARE lock over them, meaning
        users will see errors if they attempt to delete tables or edit fields. So to be
        safe you should only perform back-up's when your Baserow server is shut down
        or you have first copied the database to a new cluster which is not in active
        use.

        The back-up is split into batches as often Baserow database's can end up with
        large numbers of tables and a single run of `pg_dump` over the entire database
        will run out of shared memory and fail.
        """

    def create_parser(self, prog_name, subcommand, **kwargs):
        kwargs["add_help"] = False
        return super().create_parser(prog_name, subcommand, **kwargs)

    def add_arguments(self, parser):
        # Override the help flag so -h can be used for host like pg_dump
        parser.add_argument(
            "--help", action="help", help="Show this help message and exit."
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            dest="batch-size",
            default=60,
            help="The number of tables to back_up per each `pg_dump` command. If you "
            "are encountering out of shared memory errors then you can either "
            "lower this value or increase your databases "
            "`max_locks_per_transaction` setting. Increasing this setting will"
            "increase the speed of the back-up.",
        )
        # The arguments below are meant to match `pg_dump`s arguments in name as this
        # management command is a simple batching/looping wrapper over `pg_dump`.
        parser.add_argument(
            "-j",
            "--jobs",
            type=int,
            default=1,
            dest="jobs",
            help="Run each `pg_dump` command in parallel by dumping this number of "
            "tables simultaneously per batch back-up run. This option reduces "
            "the time of the backup but it also increases the load on the database"
            "server. Please read the `pg_dump` documentation for this argument "
            "for further details.",
        )
        parser.add_argument(
            "-f",
            "--file",
            type=str,
            dest="file",
            help="Send the backup to the specified file. If not given then "
            "backups will be saved to the working directory with a file name of "
            "`baserow_backup_{database}_{datetime}.tar.gz`",
        )
        add_shared_postgres_command_args(parser)
        parser.add_argument(
            "additional_pg_dump_args",
            nargs="*",
            help="Any further args specified after a -- will be directly "
            "passed to each call of `pg_dump` which this back_up tool "
            "runs, please see https://www.postgresql.org/docs/11/app-pgdump.html for "
            "all the available options. Please be careful as arguments provided "
            "here will override arguments passed to `pg_dump` internally by "
            "this tool such as -w, -T, -Fd and -t causing errors and undefined "
            "behavior.",
        )

    def handle(self, *args, **options):
        host = options["host"]
        database = options["database"]
        username = options["username"]
        port = options["port"]
        batch_size = options["batch-size"]
        file = options["file"]
        jobs = options["jobs"]
        additional_args = options["additional_pg_dump_args"]

        runner = BaserowBackupRunner(
            host,
            database,
            username,
            port,
            jobs,
        )
        try:
            backup_file_name = runner.backup_baserow(file, batch_size, additional_args)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully backed up Baserow to {backup_file_name} which can "
                    f"be restored using the ./baserow restore_baserow command. "
                )
            )

        except CalledProcessError as e:
            raise CommandError(
                "The back-up failed because of the failure of the following "
                "sub-command, please read the output of the failed command above to "
                "see what went wrong. \n"
                "The sub-command which failed was:\n"
                + " ".join(e.cmd)
                + f"\nIt failed with a return code of: {e.returncode}"
            )
        except InvalidBaserowBackupArchive:
            raise CommandError(
                "Please ensure the provided back-up file is a valid "
                "Baserow backup file produced by ./baserow "
                "backup_baserow"
            )

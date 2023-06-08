import subprocess  # nosec
import sys

from django.conf import settings
from django.core.management.commands.migrate import Command as MigrateCommand
from django.db import connection, transaction

from loguru import logger


class Command(MigrateCommand):
    help = (
        "Runs the migrate command wrapped in a postgres advisory lock to prevent "
        "multiple containers "
        "or processes running migrations at the same time. "
        "You should pretty much always use this command rather than the default "
        "migrate but it is critical to always use this command in any deployment of "
        "Baserow which has multiple Baserow containers or backend services running to "
        "prevent concurrency related migrations bugs."
    )

    def add_arguments(self, parser):
        # We inherit from MigrateCommand to ensure we show the exact same set of
        # command line options.
        super().add_arguments(parser)
        parser.add_argument(
            "--lock-id",
            type=int,
            default=settings.MIGRATION_LOCK_ID,
            help="Lock ID for the PostgreSQL advisory lock used to wrap the migrate "
            "command.",
        )

    def handle(self, *args, **options):
        lock_id = options["lock_id"]
        with transaction.atomic():
            self.acquire_lock(lock_id)
            self.run_migration_command()

    def acquire_lock(self, lock_id):
        with connection.cursor() as cursor:
            logger.info(
                f"Attempting to lock the postgres advisory lock with id: {lock_id} "
                "You can disable using locked_migrate by default and switch back to the "
                "non-locking version by setting BASEROW_DISABLE_LOCKED_MIGRATIONS=true."
            )
            # We are forced to use a xact lock to ensure this works properly with
            # pgbouncer, see
            # https://prog.world/synchronizing-applications-using
            # -advisory-locks-postgresql-what-is-it-why-and-the-nuances-of-working-
            # with-pgbouncer/
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])
            logger.info(f"Acquired the lock, proceeding with migration.")

    def run_migration_command(self):
        # Make sure we run the exact same migrate command just the non lock version.
        migrate_args = sys.argv.copy()
        migrate_args[migrate_args.index("locked_migrate")] = "migrate"

        # We run in a sub-process to ensure a separate database connection is made
        # as we can't run all migrations inside a single database transaction
        # which we are currently using the hold the lock.
        #
        # Nosec is added as we are a CLI tool passing through user input to a
        # sub-process, there is no danger we are intentionally doing this for it to
        # work fundamentally.
        migrate_process = subprocess.Popen(  # nosec
            migrate_args, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        self.stream_output(migrate_process.stdout, self.stdout)
        self.stream_output(migrate_process.stderr, self.stderr)
        migrate_process.wait()

        if migrate_process.returncode != 0:
            raise subprocess.CalledProcessError(
                migrate_process.returncode, migrate_args
            )

    def stream_output(self, pipe, output_stream):
        for line in iter(pipe.readline, b""):
            output_stream.write(line.decode())

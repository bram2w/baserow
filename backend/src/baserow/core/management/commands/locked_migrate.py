from django.conf import settings
from django.core.management.commands.migrate import Command as MigrateCommand
from django.db import connections, transaction

from loguru import logger

LOCKED_MIGRATE_CMD_CONNECTION_ALIAS = "locked_migrate_cmd_connection"


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
        super().add_arguments(parser)
        parser.add_argument(
            "--lock-id",
            type=int,
            default=settings.MIGRATION_LOCK_ID,
            help="Lock ID for the PostgreSQL advisory lock used to wrap the migrate "
            "command.",
        )

    def handle(self, *args, **options):
        lock_id = options.pop("lock_id")

        # We need to use a brand new, separate database connection as we need an
        # open transaction to hold the pg_advisory_xact_lock. However, we can't then
        # use this same connection to run the migrations as many of them run
        # non-atomically outside a transaction.
        separate_lock_connection = connections.create_connection("default")
        connections[LOCKED_MIGRATE_CMD_CONNECTION_ALIAS] = separate_lock_connection
        try:
            with transaction.atomic(using=LOCKED_MIGRATE_CMD_CONNECTION_ALIAS):
                self.acquire_lock(separate_lock_connection, lock_id)
                super().handle(*args, **options)
            logger.info(
                f"Migration complete, the migration lock has now been released."
            )
        finally:
            # Be sure the connection gets closed as we made it ourselves and there's
            # no harm calling close multiple times
            separate_lock_connection.close()

    def acquire_lock(self, lock_connection, lock_id):
        with lock_connection.cursor() as cursor:
            logger.info(
                f"Attempting to lock the postgres advisory lock with id: {lock_id} "
                "You can disable using locked_migrate by default and switch back to the "
                "non-locking version by setting BASEROW_DISABLE_LOCKED_MIGRATIONS=true"
            )
            # We are forced to use a xact lock to ensure this works properly with
            # pgbouncer, see
            # https://prog.world/synchronizing-applications-using
            # -advisory-locks-postgresql-what-is-it-why-and-the-nuances-of-working-
            # with-pgbouncer/
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])
            logger.info(f"Acquired the lock, proceeding with migration.")

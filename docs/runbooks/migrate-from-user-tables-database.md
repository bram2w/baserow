# Migrate From Users Tables Database Runbook

> Users who have not manually changed their default Baserow backend Django configuration
> to enable a separate `USER_TABLES_DATABASE` do not need to follow this runbook, will
> not been affected by the database inconstancy issues described below and finally do
> not need to perform any special upgrade steps for version 1.5 or later. As this
> setting is an internal undocumented Baserow setting, we believe/hope no users have
> been using this setting and this guide is primarily for internal Baserow dev
> reference.

This runbook describes how to migrate away from storing user tables in a separate user
tables database back to storing them in the same database as the rest of Baserow's
tables. If you have set the internal Baserow config parameter `USER_TABLES_DATABASE`
present in versions prior to 1.5 to connection for another database, then you are
storing the user tables in another database and must follow this migration to upgrade to
1.5 or later.

`USER_TABLES_DATABASE` was deleted as an option entirely in version 1.5 as it was
incredibly dangerous to enable. This is because any crash that happened in a transaction
after a change had been made to the `USER_TABLES_DATABASE`
would not roll back the changes in the `USER_TABLES_DATABASE`, but it would rollback
changes in the normal Baserow database. This resulted in database inconstancy issues
where Baserow believed a table/field/relation existed when in-fact it didn't, or vice
versa.

## Steps to Migrate

1. Confirm you are actually storing user tables in a separate database and need to
   follow this migration. To check this your normal Baserow database should not contain
   any `table_XXX` and `database_relation_XXX` tables. Instead you will find all of
   these tables in an entirely separate database you manually configured
   `USER_TABLES_DATABASE` to point to. Inside this other database you should see your
   user tables (`table_XXX`) and relation tables (`database_relation_XXX`). If this is
   not the case, you see all tables in your default database and in
   `backend/src/baserow/config/settings/base.py` `USER_TABLES_DATABASE` is set to
   `default` (and not overridden by other config files you might be using) then you do
   not need to follow this guide and can stop here.
1. Ensure you have taken a recoverable backup of your Baserow database.
1. Shut-down your Baserow server to ensure no further changes can be made to the
   database during the migration period.
1. Upgrade your version of Baserow, however leave the django connection pointed to by
   your `USER_TABLES_DATABASE` setting.
1. Ensure you have the command line utilities `pg_dump` and `psql` available, these can
   be installed in ubuntu by running `sudo apt install postgresql-client`
1. If you are connecting to a connection pool service like pgbouncer with your instance
   of Baserow, you need to ensure `copy_tables` will not run using a pooled connection.
    1. This is because `copy_tables` uses both `pg_dump` and `psql` which when combined
       will change the search_path of the current connection. If this happens to a
       shared pooled connection then future clients of the connection will encounter
       errors as if the Baserow tables don't exist. You must set the `DATABASE_HOST`
       , `DATABASE_PORT` and `DATABASE_NAME` environment variables before running the
       `copy_tables` command to ensure you connect directly to the database instead of
       via pg_bouncer. If you accidentally run `copy_tables` via a pooled connection you
       will need to either manually run `RESET search_path;` on that connection or reset
       that shared connection some other way.
1. Run a dry run copy by
   executing: `./baserow copy_tables --batch_size=10 --source_connection=DJANGO_CONNECTION_NAME_TO_USER_TABLES_DB --target_connection=default --dry-run`
    1. The `batch_size` parameter controls how many tables will be copied on each
       individual run of `pg_dump` and import of those tables executed by `copy_tables`.
       You can raise this value to increase the speed of the command or lower it if you
       encounter out of shared memory errors.
1. Confirm the dry run looks correct and remove `--dry-run` to the above command to
   perform the real copy.
1. Start-up your Baserow server.
1. Confirm you can see your previous databases, tables and can create new ones.
1. When confident everything is working as expected, all data has been copied and you
   have sufficient back-ups you can delete the old `USER_TABLES_DATABASE` entirely.
1. Delete the Django connection config pointed to by your old
   `USER_TABLES_DATABASE` setting and the setting itself.

## Steps to Rollback

1. Simply down-grade your version of Baserow to the previous version.
1. If you successfully ran the `copy_tables` command above your default Baserow database
   will now have a copy of all the user tables. Before attempting to migrate again you
   need to delete these copied tables otherwise when you come to repeat the command it
   will not overwrite the copies with potential new user table data. If you know the
   user tables have not been modified then this is not an issue.


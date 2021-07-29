# Back-up Baserow Runbook

## Backing Up Baserow
1. Please ensure you only back-up a Baserow database which is not actively being used
   by a running Baserow instance or any other process which is making changes to the 
   database.
1. Please create PGPASS file to store the password for your database, see
   https://www.postgresql.org/docs/11/libpq-pgpass.html for more details on this file.
1. Please read and understand the output of `./baserow backup_baserow --help`
1. Run the following command to back-up Baserow.
    `PGPASSFILE=PATH_TO_YOUR_PGPASSFILE ./baserow backup_baserow -h YOUR_DB_HOST -d YOUR_DB_NAME -U YOUR_DB_USER -p YOUR_DB_PORT`

## Restoring Baserow
1. Please ensure you never restore Baserow using a pooled connection but instead do
   the restoration via direct database connection.
1. Make a new, empty database to restore the back-up file into, please do not overwrite
   existing databases as this might cause database inconsistency errors.
1. Get a baserow backup tar gz file produced by the `./baserow backup_baserow` command 
   and its file path.
1. Please create PGPASS file to store the password for your database, see
   https://www.postgresql.org/docs/11/libpq-pgpass.html for more details on this file.
1. Please read and understand the output of `./baserow restore_baserow --help`
1. To restore Baserow run the following command: 
   `PGPASSFILE=PATH_TO_YOUR_PGPASSFILE ./baserow restore_baserow -h YOUR_DB_HOST -d YOUR_FRESH_DB_TO_RESTORE_INTO -U YOUR_DB_USER -p YOUR_DB_PORT -f PATH_TO_BACKUP_TAR_GZ` 

#!/bin/bash

startup_echo(){
    /baserow/supervisor/wrapper.sh GREEN STARTUP echo -e "\e[32m$*\e[0m"
}

init_old_data_directory () {
    startup_echo "Initialising PostgreSQL 11 data directory . . ."

    #Since postgres user is the one who will be dealing wth pg_upgrade, we need
    #to make sure it has access to the directory:
    chown postgres:postgres "${OLD}"

    /usr/lib/postgresql/11/bin/initdb \
        --encoding=UTF8 \
        --username='postgres' \
        -D ${OLD}
}

init_new_data_directory() {
    startup_echo "Initialising PostgreSQL 15 data directory . . ."

    # Check if the tmp data directory is not empty, and if not, empty it
    if [ -n "$(ls -A ${NEW})" ]; then
        rm -r "${NEW}"/*
    fi

    #Since postgres user is the one who will be dealing wth pg_upgrade, we need
    #to make sure it has access to the directory:
    chown postgres:postgres "${NEW}"

    # XXX: encoding is hardcoded:
    /usr/lib/postgresql/15/bin/initdb \
        --encoding=UTF8 \
        --username='postgres' \
        ${NEW}
}

_main() {
    startup_echo "****************************************************************************************"
    startup_echo "Existing PostgreSQL version found: ${POSTGRES_VERSION}, upgrading to PostgreSQL 15 . . ."
    startup_echo "****************************************************************************************"

    startup_echo "************************************"
    startup_echo "PostgreSQL data directory: ${PGDATA}"
    startup_echo "************************************"
    # /baserow/data/postgres

    # Check for presence of old/new directories, indicating a failed previous autoupgrade
    startup_echo "----------------------------------------------------------------------"
    startup_echo "Checking for left over artifacts from a failed previous autoupgrade..."
    startup_echo "----------------------------------------------------------------------"

    #Tmp. directory which will be used to safely back-up the existing data:
    local OLD="/baserow/data/postgres_old"
    #Tmp. directory which will be used for upgrading the data files to PostgreSQL 15:
    local NEW="/baserow/data/postgres_new"

    if [ -d "${OLD}" ]; then
        startup_echo "********************************************"
        startup_echo "Left over OLD directory found.  Removing it."
        startup_echo "********************************************"

        rm -rf "${OLD}"
    fi
    if [ -d "${NEW}" ]; then
        startup_echo "********************************************"
        startup_echo "Left over NEW directory found.  Removing it."
        startup_echo "********************************************"

        rm -rf "${NEW}"
    fi
    startup_echo "-------------------------------------------------------------------------------"
    startup_echo "No artifacts found from a failed previous autoupgrade.  Continuing the process."
    startup_echo "-------------------------------------------------------------------------------"

    # Don't automatically abort on non-0 exit status, as that messes with these upcoming mv commands
    set +e

    startup_echo "---------------------------------------"
    startup_echo "Creating OLD temporary directory ${OLD}"
    startup_echo "---------------------------------------"

    mkdir "${OLD}"

    if [ ! -d "${OLD}" ]; then
        startup_echo "*********************************************************************"
        startup_echo "Creation of temporary directory '${OLD}' failed.  Aborting completely"
        startup_echo "*********************************************************************"
        exit 7
    fi
    startup_echo "--------------------------------------------"
    startup_echo "Creating OLD temporary directory is complete"
    startup_echo "--------------------------------------------"

    #Initialising the old PostgreSQL 11 server before copying old data there:
    startup_echo "--------------------------------------------------------"
    startup_echo "Initialising the old PostgreSQL 11 server before copying"
    startup_echo "--------------------------------------------------------"
    init_old_data_directory

    startup_echo "------------------------------------------------------------------"
    startup_echo "Backing up existing data files into OLD temporary directory ${OLD}"
    startup_echo "------------------------------------------------------------------"
    cp -r "${PGDATA}"/* "${OLD}"
    startup_echo "--------------------------------------------------------------------"
    startup_echo "Copying existing data files into OLD temporary directory is complete"
    startup_echo "--------------------------------------------------------------------"

    startup_echo "---------------------------------------"
    startup_echo "Creating NEW temporary directory ${NEW}"
    startup_echo "---------------------------------------"

    mkdir "${NEW}"

    if [ ! -d "${NEW}" ]; then
        startup_echo "********************************************************************"
        startup_echo "Creation of temporary directory '${NEW}' failed. Aborting completely"
        startup_echo "********************************************************************"
        exit 8
    fi
    startup_echo "--------------------------------------------"
    startup_echo "Creating NEW temporary directory is complete"
    startup_echo "--------------------------------------------"

    # Return the error handling back to automatically aborting on non-0 exit status
    set -e

    # Initialise the new PostgreSQL database directory
    startup_echo "---------------------------------------"
    startup_echo "Initialising new PostgreSQL 15 database"
    startup_echo "---------------------------------------"
    init_new_data_directory
    startup_echo "------------------------------------"
    startup_echo "New database initialisation complete"
    startup_echo "------------------------------------"

    # Change into the PostgreSQL database directory, to avoid a pg_upgrade error about write permissions
    cd "${PGDATA}"

    # Run the pg_upgrade command itself
    startup_echo "---------------------------------------"
    startup_echo "Running pg_upgrade command, from $(pwd)"
    startup_echo "---------------------------------------"

    #Change ownership of the old data directory to postgres user again, because
    #it was reset when doing the backup of the existing database files. The
    #${NEW} directory is already owned by postgres user, because it was populated
    #during the initdb command at init_new_data_directory():
    chown -R postgres:postgres "${OLD}"
    /usr/lib/postgresql/15/bin/pg_upgrade \
        --username='postgres' \
        --link \
        -d ${OLD} \
        -D ${NEW} \
        -b /usr/lib/postgresql/11/bin \
        -B /usr/lib/postgresql/15/bin \
        -p 5433

    startup_echo "--------------------------------------"
    startup_echo "Running pg_upgrade command is complete"
    startup_echo "--------------------------------------"

    startup_echo "--------------------------------------------------------"
    startup_echo "Re-hashing user password to use SCRAM-SHA-256 encryption"
    startup_echo "--------------------------------------------------------"

    /usr/lib/postgresql/15/bin/pg_ctl \
      -D ${NEW} \
      -o "-p 5433" \
      start

    PGPASSWORD=$POSTGRES_PASSWORD /usr/lib/postgresql/15/bin/psql \
      -U postgres \
      -p 5433 \
      -d $POSTGRES_DB \
      -c "ALTER USER \"$POSTGRES_USER\" WITH PASSWORD '$POSTGRES_PASSWORD';"

    /usr/lib/postgresql/15/bin/pg_ctl \
      -D ${NEW} \
      -o "-p 5433" \
      stop

    startup_echo "-------------------------------------------------"
    startup_echo "Re-hashing user password complete, server stopped"
    startup_echo "-------------------------------------------------"

    startup_echo "----------------------------------------------------------------------------------------"
    startup_echo "Replacing the original data directory with the upgraded one which supports PostgreSQL 15"
    startup_echo "----------------------------------------------------------------------------------------"

    cp -Rf "${NEW}"/* "${PGDATA}"

    startup_echo "--------------------------------------------"
    startup_echo "Removing old temporary files and directories"
    startup_echo "--------------------------------------------"

    rm -rf "${OLD}" "${NEW}" ~/delete_old_cluster.sh

    startup_echo "-----------------------------"
    startup_echo "Changing back the permissions"
    startup_echo "-----------------------------"

    #Change back the permissions to the default data directory to postgres user,
    #because they were reset after moving the data files to the original data
    #directory (which are now compatible with PostgreSQL 15):
    chown -R postgres:postgres "${PGDATA}"

    startup_echo "------------------------------------------------------------------"
    startup_echo "*** Upgrading from PostgreSQL 11 to PostgreSQL 15 is complete! ***"
    startup_echo "------------------------------------------------------------------"
    exit 10
}

_main "$@"

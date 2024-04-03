#!/bin/bash

# This script is heavily inspired by https://github.com/pgautoupgrade/docker-pgautoupgrade/blob/main/docker-entrypoint.sh
# with some modifications to fit the Baserow use case.

startup_echo(){
    /baserow/supervisor/wrapper.sh GREEN STARTUP echo -e "\e[32m$*\e[0m"
}

init_data_directory() {
    local data_dir=$1

    startup_echo "Initialising PostgreSQL ${POSTGRES_VERSION} data directory . . ."

    # Check if the data directory is not empty, and if not, empty it
    if [ -n "$(ls -A ${data_dir})" ]; then
        rm -r "${data_dir}"/*
    fi

    "${POSTGRES_BIN_FOLDER}/initdb" \
        --encoding=UTF8 \
        --username='postgres' \
        -D "${data_dir}"
}

_main() {
    startup_echo "****************************************************************************************"
    startup_echo "Existing PostgreSQL version found: ${POSTGRES_OLD_VERSION}, upgrading to PostgreSQL ${POSTGRES_VERSION} ..."
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
    local OLD="${PGAUTOUPGRADE_DIR}/${POSTGRES_OLD_VERSION}"
    #Tmp. directory which will be used for upgrading the data files to the new version:
    local NEW="${PGAUTOUPGRADE_DIR}/${POSTGRES_VERSION}"

    if [ -d "${OLD}" ]; then
        startup_echo "***************************************"
        startup_echo "Left over OLD directory found. Exiting."
        startup_echo "***************************************"

        exit 2
    fi
    if [ -d "${NEW}" ]; then
        startup_echo "***************************************"
        startup_echo "Left over NEW directory found. Exiting."
        startup_echo "***************************************"

        exit 3
    fi
    startup_echo "-------------------------------------------------------------------------------"
    startup_echo "No artifacts found from a failed previous autoupgrade.  Continuing the process."
    startup_echo "-------------------------------------------------------------------------------"

    # Don't automatically abort on non-0 exit status, as that messes with these upcoming mv commands
    set +e

    startup_echo "---------------------------------------"
    startup_echo "Creating OLD temporary directory ${OLD}"
    startup_echo "---------------------------------------"

    mkdir -m 700 "${OLD}"

    if [ ! -d "${OLD}" ]; then
        startup_echo "*********************************************************************"
        startup_echo "Creation of temporary directory '${OLD}' failed.  Aborting completely"
        startup_echo "*********************************************************************"
        exit 4
    fi
    startup_echo "--------------------------------------------"
    startup_echo "Creating OLD temporary directory is complete"
    startup_echo "--------------------------------------------"

    startup_echo "--------------------------------------------------------------"
    startup_echo "Moving existing data files into OLD temporary directory ${OLD}"
    startup_echo "--------------------------------------------------------------"
    mv -v "${PGDATA}"/* "${OLD}"
    startup_echo "--------------------------------------------------------------------"
    startup_echo "Copying existing data files into OLD temporary directory is complete"
    startup_echo "--------------------------------------------------------------------"

    startup_echo "---------------------------------------"
    startup_echo "Creating NEW temporary directory ${NEW}"
    startup_echo "---------------------------------------"

    mkdir -m 700 "${NEW}"

    if [ ! -d "${NEW}" ]; then
        startup_echo "********************************************************************"
        startup_echo "Creation of temporary directory '${NEW}' failed. Aborting completely"
        startup_echo "********************************************************************"
        # With a failure at this point we should be able to move the old data back
        # to its original location
        mv -v "${OLD}"/* "${PGDATA}"
        exit 5
    fi
    startup_echo "--------------------------------------------"
    startup_echo "Creating NEW temporary directory is complete"
    startup_echo "--------------------------------------------"

    # Return the error handling back to automatically aborting on non-0 exit status
    set -e

    startup_echo "--------------------------------------------------------------------------------"
    startup_echo "Updating PostgreSQL configuration files to point at the correct data directories"
    startup_echo "--------------------------------------------------------------------------------"

    sed -i "s;/var/lib/postgresql/${POSTGRES_OLD_VERSION}/main;$OLD;g" ${POSTGRES_OLD_LOCATION}/postgresql.conf
    sed -i "s;${PGDATA%/};${NEW};g" ${POSTGRES_LOCATION}/postgresql.conf

    startup_echo "------------------------------------------------"
    startup_echo "Updating PostgreSQL configuration files complete"
    startup_echo "------------------------------------------------"

    # Initialise the new PostgreSQL database directory
    startup_echo "---------------------------------------"
    startup_echo "Initialising new PostgreSQL ${POSTGRES_VERSION} database"
    startup_echo "---------------------------------------"
    init_data_directory "${NEW}"
    startup_echo "------------------------------------"
    startup_echo "New database initialisation complete"
    startup_echo "------------------------------------"

    # Change into the PostgreSQL database directory, to avoid a pg_upgrade error about write permissions
    cd "${PGDATA}"

    startup_echo "--------------------------------"
    startup_echo "Running pg_upgrade check command"
    startup_echo "--------------------------------"

    ${POSTGRES_BIN_FOLDER}/pg_upgrade \
        --check \
        --username='postgres' \
        --link \
        -d ${OLD} \
        -D ${NEW} \
        -b ${POSTGRES_OLD_BIN_FOLDER} \
        -B ${POSTGRES_BIN_FOLDER} \
        -o "-c config_file=${POSTGRES_OLD_LOCATION}/postgresql.conf" \
        -O "-c config_file=${POSTGRES_LOCATION}/postgresql.conf"

    if [ $? -ne 0 ]; then
      startup_echo "----------------------------------------------------------"
      startup_echo "pg_upgrade check failed. Refer to `pg_upgrade` documentation at https://www.postgresql.org/docs/current/pgupgrade.html, Baserow community at https://community.baserow.io/ or contact Baserow support for assistance."
      startup_echo "----------------------------------------------------------"
      exit 6
    fi

    # Run the pg_upgrade command itself
    startup_echo "---------------------------------------"
    startup_echo "Running pg_upgrade command, from $(pwd)"
    startup_echo "---------------------------------------"

    ${POSTGRES_BIN_FOLDER}/pg_upgrade \
        --username='postgres' \
        --link \
        -d ${OLD} \
        -D ${NEW} \
        -b ${POSTGRES_OLD_BIN_FOLDER} \
        -B ${POSTGRES_BIN_FOLDER} \
        -o "-c config_file=${POSTGRES_OLD_LOCATION}/postgresql.conf" \
        -O "-c config_file=${POSTGRES_LOCATION}/postgresql.conf"

    startup_echo "--------------------------------------"
    startup_echo "Running pg_upgrade command is complete"
    startup_echo "--------------------------------------"

    # TODO for future upgrades: check if the next step is necessary
    startup_echo "--------------------------------------------------------"
    startup_echo "Re-hashing user password to use new default SCRAM-SHA-256 encryption"
    startup_echo "--------------------------------------------------------"

    ${POSTGRES_BIN_FOLDER}/pg_ctl \
      -D ${NEW} \
      start

    PGPASSWORD=$POSTGRES_PASSWORD ${POSTGRES_BIN_FOLDER}/psql \
      -U postgres \
      -d $POSTGRES_DB \
      -c "ALTER USER \"$POSTGRES_USER\" WITH PASSWORD '$POSTGRES_PASSWORD';"

    ${POSTGRES_BIN_FOLDER}/pg_ctl \
      -D ${NEW} \
      stop

    startup_echo "-------------------------------------------------"
    startup_echo "Re-hashing user password complete, server stopped"
    startup_echo "-------------------------------------------------"

    startup_echo "----------------------------------------------------------------------------------------"
    startup_echo "Replacing the original data directory with the upgraded one which supports PostgreSQL ${POSTGRES_VERSION}"
    startup_echo "----------------------------------------------------------------------------------------"

    mv -v "${NEW}"/* "${PGDATA}"

    if [ -f "${OLD}/baserow_db_setup" ]; then
      startup_echo "------------------------------------------"
      startup_echo "Moving the Baserow DB setup indicator file"
      startup_echo "------------------------------------------"
      mv -v "${OLD}/baserow_db_setup" "${PGDATA}/"
    fi

    startup_echo "*************************"
    startup_echo "*** Upgrade complete. ***"
    startup_echo "*************************"
}

_main "$@"

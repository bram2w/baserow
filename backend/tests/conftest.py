from __future__ import print_function
import psycopg2
import pytest
from django.db import connections
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys


@pytest.fixture
def data_fixture():
    from .fixtures import Fixtures

    return Fixtures()


@pytest.fixture()
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


# We reuse this file in the premium backend folder, if you run a pytest session over
# plugins and the core at the same time pytest will crash if this called multiple times.
def pytest_addoption(parser):
    # Unfortunately a simple decorator doesn't work here as pytest is doing some
    # exciting reflection of sorts over this function and crashes if it is wrapped.
    if not hasattr(pytest_addoption, "already_run"):
        parser.addoption(
            "--runslow", action="store_true", default=False, help="run slow tests"
        )
        pytest_addoption.already_run = True


def pytest_configure(config):
    if not hasattr(pytest_configure, "already_run"):
        config.addinivalue_line("markers", "slow: mark test as slow to run")
        pytest_configure.already_run = True


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def run_non_transactional_raw_sql(sqls, dbinfo):
    conn = psycopg2.connect(
        host=dbinfo["HOST"],
        user=dbinfo["USER"],
        password=dbinfo["PASSWORD"],
        port=int(dbinfo["PORT"]),
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    for sql in sqls:
        cursor.execute(sql)

    conn.close()


# Nicest way of printing to stderr sourced from
# https://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@pytest.fixture()
def user_tables_in_separate_db(settings):
    """
    Creates a temporary database and sets up baserow so it is used to store user tables.

    Currently this has only been implemented at a function level scope as adding
    databases to settings.DATABASES causes pytest to assume they are extra replica dbs
    and spend ages setting them up as mirrors. Instead keeping this at the functional
    scope lets us keep it simple and quick.
    """

    default_db = settings.DATABASES["default"]
    user_table_db_name = f'{default_db["NAME"]}_user_tables'

    # Print to stderr to match pytest-django's behaviour for logging about test
    # database setup and teardown.
    eprint(f"Dropping and recreating {user_table_db_name} for test.")

    settings.USER_TABLE_DATABASE = "user_tables_database"
    settings.DATABASES["user_tables_database"] = dict(default_db)
    settings.DATABASES["user_tables_database"]["NAME"] = user_table_db_name

    # You cannot drop databases inside transactions and django provides no easy way
    # of turning them off temporarily. Instead we need to open our own connection so
    # we can turn off transactions to perform the required setup/teardown sql. See:
    # https://pytest-django.readthedocs.io/en/latest/database.html#using-a-template
    # -database-for-tests
    run_non_transactional_raw_sql(
        [
            f"DROP DATABASE IF EXISTS {user_table_db_name}; ",
            f"CREATE DATABASE {user_table_db_name}",
        ],
        default_db,
    )

    yield connections["user_tables_database"]

    # Close django's connection to the user table db so we can drop it.
    connections["user_tables_database"].close()

    run_non_transactional_raw_sql([f"DROP DATABASE {user_table_db_name}"], default_db)

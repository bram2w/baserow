from __future__ import print_function

import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


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

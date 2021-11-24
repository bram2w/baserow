import os

import pytest
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS


@pytest.fixture
def data_fixture():
    from .fixtures import Fixtures

    return Fixtures()


@pytest.fixture()
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture()
def environ():
    original_env = os.environ.copy()
    yield os.environ
    for key, value in original_env.items():
        os.environ[key] = value


@pytest.fixture()
def mutable_field_type_registry():
    from baserow.contrib.database.fields.registries import field_type_registry

    before = field_type_registry.registry.copy()
    yield field_type_registry
    field_type_registry.registry = before


@pytest.fixture()
def migrate_to_latest_at_end():
    yield
    # We need to apply the latest migration otherwise other tests might fail.
    call_command("migrate", verbosity=0, database=DEFAULT_DB_ALIAS)


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

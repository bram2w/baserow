import contextlib
import os

from django.apps import apps
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS

import pytest

from baserow.core.apps import sync_operations_after_migrate
from baserow_enterprise.apps import sync_default_roles_after_migrate

SKIP_FLAGS = ["disabled-in-ci", "once-per-day-in-ci"]
COMMAND_LINE_FLAG_PREFIX = "--run-"


@pytest.fixture
def data_fixture():
    from .fixtures import Fixtures

    return Fixtures()


@pytest.fixture
def synced_roles(db):
    sync_operations_after_migrate(None, apps=apps)
    sync_default_roles_after_migrate(None, apps=apps)


@pytest.fixture()
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture(scope="module")
def reset_schema_after_module(request, django_db_setup, django_db_blocker):
    yield
    with django_db_blocker.unblock():
        call_command("migrate", verbosity=0, database=DEFAULT_DB_ALIAS)


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
def mutable_action_registry():
    from baserow.core.action.registries import action_type_registry

    before = action_type_registry.registry.copy()
    yield action_type_registry
    action_type_registry.registry = before


@pytest.fixture()
def patch_filefield_storage(tmpdir):
    """
    Patches all filefield storages from all models with the one given in parameter
    or a newly created one.
    """

    from django.apps import apps
    from django.core.files.storage import FileSystemStorage
    from django.db.models import FileField

    # Cache the storage
    _storage = None

    @contextlib.contextmanager
    def patch(new_storage=None):
        nonlocal _storage
        if new_storage is None:
            if not _storage:
                # Create a default storage if none given
                _storage = FileSystemStorage(
                    location=str(tmpdir), base_url="http://localhost"
                )
            new_storage = _storage

        previous_storages = {}
        # Replace storage
        for model in apps.get_models():
            filefields = (f for f in model._meta.fields if isinstance(f, FileField))
            for filefield in filefields:
                previous_storages[
                    f"{model._meta.label}_{filefield.name}"
                ] = filefield.storage
                filefield.storage = new_storage

        yield new_storage

        # Restore previous storage
        for model in apps.get_models():
            filefields = (f for f in model._meta.fields if isinstance(f, FileField))

            for filefield in filefields:
                filefield.storage = previous_storages[
                    f"{model._meta.label}_{filefield.name}"
                ]

    return patch


# We reuse this file in the premium/enterprise backend folder, if you run a pytest
# session over plugins and the core at the same time pytest will crash if this
# called multiple times.
def pytest_addoption(parser):
    # Unfortunately a simple decorator doesn't work here as pytest is doing some
    # exciting reflection of sorts over this function and crashes if it is wrapped.
    if not hasattr(pytest_addoption, "already_run"):
        for flag in SKIP_FLAGS:
            parser.addoption(
                f"{COMMAND_LINE_FLAG_PREFIX}{flag}",
                action="store_true",
                default=False,
                help=f"run {flag} tests",
            )
        pytest_addoption.already_run = True


def pytest_configure(config):
    if not hasattr(pytest_configure, "already_run"):
        for flag in SKIP_FLAGS:
            config.addinivalue_line(
                "markers",
                f"{flag}: mark test so it only runs when the "
                f"{COMMAND_LINE_FLAG_PREFIX}{flag} flag is provided to pytest",
            )
        pytest_configure.already_run = True


def pytest_collection_modifyitems(config, items):
    enabled_flags = {
        flag
        for flag in SKIP_FLAGS
        if config.getoption(f"{COMMAND_LINE_FLAG_PREFIX}{flag}")
    }
    for item in items:
        for flag in SKIP_FLAGS:
            flag_for_python = flag.replace("-", "_")
            if flag_for_python in item.keywords and flag not in enabled_flags:
                skip_marker = pytest.mark.skip(
                    reason=f"need {COMMAND_LINE_FLAG_PREFIX}{flag} option to run"
                )
                item.add_marker(skip_marker)
                break

import asyncio
import contextlib
import os
from pathlib import Path
from typing import Dict, Optional

from django.conf import settings
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, OperationalError

import pytest
from pyinstrument import Profiler

from baserow.contrib.database.application_types import DatabaseApplicationType
from baserow.core.permission_manager import CorePermissionManagerType
from baserow.core.trash.trash_types import GroupTrashableItemType

SKIP_FLAGS = ["disabled-in-ci", "once-per-day-in-ci"]
COMMAND_LINE_FLAG_PREFIX = "--run-"


# We need to manually deal with the event loop since we are using asyncio in the
# tests in this directory and they have some issues when it comes to pytest.
# This solution is taken from: https://bit.ly/3UJ90co
@pytest.fixture(scope="session")
def async_event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def data_fixture():
    from .fixtures import Fixtures

    return Fixtures()


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
    field_type_registry.get_for_class.cache_clear()
    yield field_type_registry
    field_type_registry.get_for_class.cache_clear()
    field_type_registry.registry = before


@pytest.fixture()
def mutable_action_registry():
    from baserow.core.action.registries import action_type_registry

    before = action_type_registry.registry.copy()
    yield action_type_registry
    action_type_registry.registry = before


@pytest.fixture
def mutable_application_registry():
    from baserow.core.registries import application_type_registry

    before = application_type_registry.registry.copy()
    application_type_registry.get_for_class.cache_clear()
    yield application_type_registry
    application_type_registry.get_for_class.cache_clear()
    application_type_registry.registry = before


@pytest.fixture
def mutable_trash_item_type_registry():
    from baserow.core.trash.registries import trash_item_type_registry

    before = trash_item_type_registry.registry.copy()
    trash_item_type_registry.get_for_class.cache_clear()
    yield trash_item_type_registry
    trash_item_type_registry.get_for_class.cache_clear()
    trash_item_type_registry.registry = before


@pytest.fixture
def mutable_permission_manager_registry():
    from baserow.core.registries import permission_manager_type_registry

    before = permission_manager_type_registry.registry.copy()
    yield permission_manager_type_registry
    permission_manager_type_registry.registry = before


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


@pytest.fixture()
def profiler():
    """
    A fixture to provide an easy way to profile code in your tests.
    """

    TESTS_ROOT = Path.cwd()
    PROFILE_ROOT = TESTS_ROOT / ".profiles"
    profiler = Profiler()

    @contextlib.contextmanager
    def profile_this(
        print_result: bool = True,
        html_report_name: str = "",
        output_text_params: Optional[Dict] = None,
        output_html_params: Optional[Dict] = None,
    ):
        """
        Context manager to profile something.
        """

        profiler.start()

        yield profiler

        profiler.stop()

        output_text_params = output_text_params or {}
        output_html_params = output_html_params or {}

        output_text_params.setdefault("unicode", True)
        output_text_params.setdefault("color", True)

        if print_result:
            print(profiler.output_text(**output_text_params))

        if html_report_name:
            PROFILE_ROOT.mkdir(exist_ok=True)
            results_file = PROFILE_ROOT / f"{html_report_name}.html"
            with open(results_file, "w", encoding="utf-8") as f_html:
                f_html.write(profiler.output_html(**output_html_params))

        profiler.reset()

    return profile_this


class BaseMaxLocksPerTransactionStub:
    # Determines whether we raise an `OperationalError` about
    # `max_locks_per_transaction` or something else.
    raise_transaction_exception: bool = True

    def get_message(self) -> str:
        message = "An operational error has occurred."
        if self.raise_transaction_exception:
            message = "HINT:  You might need to increase max_locks_per_transaction."
        return message


class MaxLocksPerTransactionExceededApplicationType(
    DatabaseApplicationType, BaseMaxLocksPerTransactionStub
):
    def export_serialized(self, *args, **kwargs):
        raise OperationalError(self.get_message())


class MaxLocksPerTransactionExceededGroupTrashableItemType(
    GroupTrashableItemType, BaseMaxLocksPerTransactionStub
):
    def permanently_delete_item(self, *args, **kwargs):
        raise OperationalError(self.get_message())


@pytest.fixture
def application_type_serialized_raising_operationalerror(
    mutable_application_registry,
) -> callable:
    """
    Overrides the existing `DatabaseApplicationType` with a test only stub version that
    optionally (if `raise_transaction_exception` is `True`) raises an `OperationalError`
    about `max_locks_per_transaction` being exceeded when `export_serialized` is called.
    """

    @contextlib.contextmanager
    def _perform_stub(raise_transaction_exception: bool = True):
        stub_application_type = MaxLocksPerTransactionExceededApplicationType()
        stub_application_type.raise_transaction_exception = raise_transaction_exception
        mutable_application_registry.get_for_class.cache_clear()
        mutable_application_registry.registry[
            DatabaseApplicationType.type
        ] = stub_application_type

        yield stub_application_type

    return _perform_stub


@pytest.fixture
def trash_item_type_perm_delete_item_raising_operationalerror(
    mutable_trash_item_type_registry,
) -> callable:
    """
    Overrides the existing `GroupTrashableItemType` with a test only stub version that
    optionally (if `raise_transaction_exception` is `True`) raises an `OperationalError`
    about `max_locks_per_transaction` being exceeded when `permanently_delete_item`
    is called.
    """

    @contextlib.contextmanager
    def _perform_stub(raise_transaction_exception: bool = True):
        stub_trash_item_type = MaxLocksPerTransactionExceededGroupTrashableItemType()
        stub_trash_item_type.raise_transaction_exception = raise_transaction_exception
        mutable_trash_item_type_registry.get_for_class.cache_clear()
        mutable_trash_item_type_registry.registry[
            GroupTrashableItemType.type
        ] = stub_trash_item_type

        yield stub_trash_item_type

    return _perform_stub


class StubbedCorePermissionManagerType(CorePermissionManagerType):
    def check_permissions(
        self, actor, operation, group=None, context=None, include_trash=False
    ):
        return True


@pytest.fixture
def bypass_check_permissions(
    mutable_permission_manager_registry,
) -> CorePermissionManagerType:
    """
    Overrides the existing `CorePermissionManagerType` so that
    we can always `return True` on a `check_permissions` call.
    """

    stub_core_permission_manager = StubbedCorePermissionManagerType()
    first_manager = settings.PERMISSION_MANAGERS[0]
    mutable_permission_manager_registry.registry[
        first_manager
    ] = stub_core_permission_manager
    yield stub_core_permission_manager

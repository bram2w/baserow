from __future__ import print_function

from django.core.management import call_command
from django.db import connections
from django.test.testcases import TransactionTestCase

# noinspection PyUnresolvedReferences
from baserow.test_utils.pytest_conftest import *  # noqa: F403, F401


def _fixture_teardown(self):
    """
    This is a custom implementation of `TransactionTestCase._fixture_teardown`
    from Django (https://github.com/django/django/blob/main/django/test/testcases.py)
    that flushes test database after test runs with allow_cascade=True.

    This is needed as our custom Baserow tables won't be in the list of tables
    to truncate, and hence may create problems when rows are
    referencing other tables.
    """

    # Allow TRUNCATE ... CASCADE and don't emit the post_migrate signal
    # when flushing only a subset of the apps
    for db_name in self._databases_names(include_mirrors=False):
        # Flush the database
        inhibit_post_migrate = (
            self.available_apps is not None
            or (  # Inhibit the post_migrate signal when using serialized
                # rollback to avoid trying to recreate the serialized data.
                self.serialized_rollback
                and hasattr(connections[db_name], "_test_serialized_contents")
            )
        )
        call_command(
            "flush",
            verbosity=0,
            interactive=False,
            database=db_name,
            reset_sequences=False,
            allow_cascade=True,  # CHANGED FROM DJANGO
            inhibit_post_migrate=inhibit_post_migrate,
        )


TransactionTestCase._fixture_teardown = _fixture_teardown

from contextlib import contextmanager
from functools import wraps

from django.db.transaction import get_connection

from cachalot import utils as cachalot_utils
from cachalot.settings import cachalot_settings
from psycopg2.sql import Composed


@contextmanager
def cachalot_enabled():
    """
    A context manager that enables cachalot for the duration of the context. This is
    useful when you want to enable cachalot for a specific query but you don't want
    to enable it globally.
    Please note that the query have to be executed within the context of the context
    manager in order for it to be cached.
    """

    from cachalot.api import LOCAL_STORAGE

    was_enabled = getattr(
        LOCAL_STORAGE, "cachalot_enabled", cachalot_settings.CACHALOT_ENABLED
    )
    LOCAL_STORAGE.cachalot_enabled = True
    try:
        yield
    finally:
        LOCAL_STORAGE.cachalot_enabled = was_enabled


def patch_cachalot_for_baserow():
    """
    This function patches the cachalot library to make it work with baserow
    dynamic models. The problem we're trying to solve here is that the only way
    to limit what cachalot caches is to provide a fix list of tables, but
    baserow creates dynamic models on the fly so we can't know what tables will
    be created in advance, so we need to include all the tables that start with
    the USER_TABLE_DATABASE_NAME_PREFIX prefix in the list of cachable tables.

    `filter_cachable` and `is_cachable` are called to invalidate the cache when
    a table is changed. `are_all_cachable` is called to check if a query can be
    cached.
    """

    from baserow.contrib.database.table.constants import USER_TABLE_DATABASE_NAME_PREFIX

    original_filter_cachable = cachalot_utils.filter_cachable
    baserow_table_name_prefix = USER_TABLE_DATABASE_NAME_PREFIX

    @wraps(original_filter_cachable)
    def patched_filter_cachable(tables):
        return original_filter_cachable(tables).union(
            set(filter(lambda t: t.startswith(baserow_table_name_prefix), tables))
        )

    cachalot_utils.filter_cachable = patched_filter_cachable

    original_is_cachable = cachalot_utils.is_cachable

    @wraps(original_is_cachable)
    def patched_is_cachable(table):
        is_baserow_table = table.startswith(baserow_table_name_prefix)
        return is_baserow_table or original_is_cachable(table)

    cachalot_utils.is_cachable = patched_is_cachable

    original_are_all_cachable = cachalot_utils.are_all_cachable

    @wraps(original_are_all_cachable)
    def patched_are_all_cachable(tables):
        """
        This patch works because cachalot does not explicitly set this thread
        local variable, but it assumes to be True by default if CACHALOT_ENABLED
        is not set otherwise. Since we are explicitly setting it to True in our
        code for the query we want to cache, we can check if the value has been
        set or not to exclude our dynamic tables from the list of tables that
        cachalot will check, making all of them cachable for the queries
        wrapped in the `cachalot_enabled` context manager.
        """

        from cachalot.api import LOCAL_STORAGE

        cachalot_enabled = getattr(LOCAL_STORAGE, "cachalot_enabled", False)
        if cachalot_enabled:
            tables = set(
                t for t in tables if not t.startswith(baserow_table_name_prefix)
            )
        return original_are_all_cachable(tables)

    cachalot_utils.are_all_cachable = patched_are_all_cachable

    def lower(self):
        """
        Cachalot wants this method to lowercase the queries to check if they are
        cachable, but the Composed class in psycopg2.sql does not have a lower
        method, so we add it here to add the support for it.
        """

        cursor = get_connection().cursor()
        return self.as_string(cursor.cursor).lower()

    Composed.lower = lower

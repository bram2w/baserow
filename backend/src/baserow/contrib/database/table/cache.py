"""
This file is responsible for caching Table model field attrs. These field attrs are
stored in the generated models cache in a Redis backed Django cache (or in-memory cache
for tests).

Every table can have a model version stored in the
`full_table_model_version_{table_id}_{BASEROW_VERSION}` cache key. This model version
starts at 0 and is incremented every time:
1. A change is made to the table or one of its fields.
2. A process generates a new field_attrs for caching by querying the database.

We then store cache field_attrs in the cache key:
    `full_table_model_{table_id}_{min_model_version}_{BASEROW_VERSION}`

When we construct a model we:
1. Get the latest model version
2. Get that model versions field_attrs from the cache


By using different keys for different versions of the model we can
be sure concurrent changes to the model aren't going to overwrite each others
changes to the cached field_attrs.
"""

from typing import Dict, Any, Optional

from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured

from baserow.version import VERSION as BASEROW_VERSION

generated_models_cache = caches[settings.GENERATED_MODEL_CACHE_NAME]


def table_model_cache_version_key(table_id: int) -> str:
    return f"full_table_model_version_{table_id}_{BASEROW_VERSION}"


def table_model_cache_entry_key(table_id: int) -> str:
    return f"full_table_model_{table_id}_{BASEROW_VERSION}"


def get_cached_model_field_attrs(
    table_id: int, min_model_version: int
) -> Optional[Dict[str, Any]]:
    """
    :param min_model_version: The model version to lookup, if an older or no version is
        found then None will be returned. Use get_current_cached_model_version to get
        this value.
    :param table_id: The table to lookup any cached mode field attrs for.
    :return: The latest cached field attrs for the table's model or None if nothing has
        been cached yet or the attrs in the cache are older than the provided min
        version.
    """

    cache_key = table_model_cache_entry_key(table_id)

    cache_entry = generated_models_cache.get(cache_key)
    if cache_entry and cache_entry["version"] >= min_model_version:
        return cache_entry["field_attrs"]
    else:
        return None


def get_current_cached_model_version(table_id: int) -> int:
    """
    Returns the current cached model version for the table id. This can be then used
    when getting the cached model attrs using the get_cached_model_field_attrs method.
    """

    model_version_key = table_model_cache_version_key(table_id)
    return generated_models_cache.get_or_set(model_version_key, 0, timeout=None)


def set_cached_model_field_attrs(
    table_id: int, model_version: int, field_attrs: Dict[str, Any]
):
    """
    Will increment the latest model version for table_id and store field_attrs in the
    cache entry for that model version.

    :param table_id: The table to lookup any cached mode field attrs for.
    :param model_version: The version of the model being set in the cache.
    :param field_attrs: The field_attrs for table_id to cache.
    """

    cache_key = table_model_cache_entry_key(table_id)
    generated_models_cache.set(
        cache_key,
        {"field_attrs": field_attrs, "version": model_version},
        timeout=None,
    )


def clear_generated_model_cache():
    print("Clearing Baserow's internal generated model cache...")
    if hasattr(generated_models_cache, "delete_pattern"):
        generated_models_cache.delete_pattern("full_table_model_*")
    elif settings.TESTS:
        # Just clear the entire cache in tests
        generated_models_cache.clear()
    else:
        raise ImproperlyConfigured(
            "Baserow must be run with a redis cache outside of " "tests."
        )
    print("Done clearing cache.")


def invalidate_table_in_model_cache(
    table_id: int, invalidate_related_tables: bool = False
):
    """
    Invalidates all versions of tables model for all versions of Baserow in the model
    cache.

    If invalidate_related_tables is True then first calls
    field_type.before_table_model_invalidated on every field in the table. This
    field_type method will then trigger further invalidations of the model cache for
    other tables if need be.
    """

    if invalidate_related_tables:
        _invalidate_all_related_models(table_id)

    model_version_key = table_model_cache_version_key(table_id)
    _incr_or_create_key_atomically_if_possible(model_version_key)


def _incr_or_create_key_atomically_if_possible(key_to_incr: str) -> int:
    """
    Attempts to increment the provided key if present or otherwise create it in an
    atomic fashion.

    If the cache backend does not support the "ignore_key_check" parameter required
    to do an atomic incr/create then we fall back to a non-atomic incr and create.
    """

    try:
        return generated_models_cache.incr(key_to_incr, ignore_key_check=True)
    except TypeError:
        # We are using a cache backend that doesn't support ignore_key_check so we can't
        # do an atomic increment or create. Instead we do our best and incr/set
        # separately
        try:
            return generated_models_cache.incr(key_to_incr)
        except ValueError:
            generated_models_cache.set(key_to_incr, 1, timeout=None)
            return 1


def _invalidate_all_related_models(table_id: int):
    """
    Given a table id looks up the latest cached field_attrs for it and loops over
    all of the fields found in the field_attrs calling their
    before_table_model_invalidated hook. Then in the link row field this hook will
    recursively invalidate the linked table.

    We need to do this as a change in one tables model might invalidate the cached
    models of any related tables.

    :param table_id: The table to invalidate all other table models which are related
        via link row fields to this table via.
    """

    from baserow.contrib.database.fields.registries import field_type_registry

    this_version_cache_key = table_model_cache_entry_key(table_id)

    try:
        field_objects = generated_models_cache.get(this_version_cache_key, {})[
            "field_attrs"
        ]["_field_objects"]
    except KeyError:
        field_objects = {}

    for field_obj in field_objects.values():
        field = field_obj.get("field", None)
        if field is not None:
            field_type = field_type_registry.get_by_model(field)
            field_type.before_table_model_invalidated(field)

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
    `full_table_model_{table_id}_{model_version}_{BASEROW_VERSION}`

When we construct a model we:
1. Get the latest model version
2. Get that model versions field_attrs from the cache


By using different keys for different versions of the model we can
be sure concurrent changes to the model aren't going to overwrite each others
changes to the cached field_attrs.
"""

from typing import Dict, Any

from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured

from baserow.version import VERSION as BASEROW_VERSION

generated_models_cache = caches[settings.GENERATED_MODEL_CACHE_NAME]


def table_model_cache_version_key(table_id: int) -> str:
    return f"full_table_model_version_{table_id}_{BASEROW_VERSION}"


def table_model_cache_entry_key(table_id: int, model_version: int) -> str:
    return f"full_table_model_{table_id}_{model_version}_{BASEROW_VERSION}"


def all_model_version_table_model_cache_entry_key(table_id: int) -> str:
    return f"full_table_model_{table_id}_*"


def get_latest_cached_model_field_attrs(table_id: int) -> Dict[str, Any]:
    """
    :param table_id: The table to lookup any cached mode field attrs for.
    :return: The latest cached field attrs for the table's model or None if nothing has
        been cached yet.
    """

    model_version_key = table_model_cache_version_key(table_id)
    latest_model_version = generated_models_cache.get_or_set(
        model_version_key, 0, timeout=None
    )

    cache_key = table_model_cache_entry_key(table_id, latest_model_version)

    return generated_models_cache.get(cache_key)


def set_cached_model_field_attrs(table_id: int, field_attrs: Dict[str, Any]):
    """
    Will increment the latest model version for table_id and store field_attrs in the
    cache entry for that model version.

    :param table_id: The table to lookup any cached mode field attrs for.
    :param field_attrs: The field_attrs for table_id to cache.
    """

    model_version_key = table_model_cache_version_key(table_id)
    # We are setting a new version of the tables field_attrs, we incr here again to
    # ensure `next_model_version` is unique to this process and no other concurrent
    # process will ever override what we are about to set.
    # If we did not do this two different processes could get the same
    # `next_model_version` and then race to set field_attrs. Both processes could have
    # queried the database at different times and constructed different field_attrs.
    next_model_version = generated_models_cache.incr(model_version_key)
    cache_key = table_model_cache_entry_key(table_id, next_model_version)
    generated_models_cache.set(cache_key, field_attrs, timeout=None)


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

    model_version_key = table_model_cache_version_key(table_id)
    model_version = generated_models_cache.get_or_set(model_version_key, 0)

    if invalidate_related_tables:
        _invalidate_all_related_models(table_id, model_version)

    if hasattr(generated_models_cache, "delete_pattern"):
        all_versions_cache_key = all_model_version_table_model_cache_entry_key(table_id)
        # By deleting all versions we clean up any old versions left in the cache.
        generated_models_cache.delete_pattern(all_versions_cache_key)
    else:
        generated_models_cache.delete(
            table_model_cache_entry_key(table_id, model_version)
        )

    generated_models_cache.incr(model_version_key)

    return model_version


def _invalidate_all_related_models(table_id: int, related_model_version: int):
    from baserow.contrib.database.fields.registries import field_type_registry

    this_version_cache_key = table_model_cache_entry_key(
        table_id, related_model_version
    )
    field_attrs = generated_models_cache.get(this_version_cache_key)
    if field_attrs is not None:
        for field_obj in field_attrs.get("_field_objects", []).values():
            field = field_obj.get("field", None)
            if field is not None:
                field_type = field_type_registry.get_by_model(field)
                field_type.before_table_model_invalidated(field)

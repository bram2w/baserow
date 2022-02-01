from django.conf import settings
from django.core.cache import caches

from baserow.version import VERSION

generated_models_cache = caches[settings.GENERATED_MODEL_CACHE_NAME]


def table_model_cache_entry_key(table_id: int):
    return f"full_table_model_{table_id}_{VERSION}"


def all_baserow_version_table_model_cache_entry_key(table_id: int):
    return f"full_table_model_{table_id}_*"


def clear_generated_model_cache():
    print("Clearing Baserow's internal generated model cache...")
    generated_models_cache.clear()
    print("Done clearing cache.")


def invalidate_table_model_cache_and_related_models(table_id: int):
    """
    Invalidates table_id's table model and all related models by calling
    field_type.before_table_model_invalidated on every field in the table referred to
    by table_id.
    """

    _invalidate_all_related_models(table_id)

    invalidate_single_table_in_model_cache(table_id)


def invalidate_single_table_in_model_cache(table_id: int):
    """
    Invalidates a single model in the model cache for all versions of Baserow. Does not
    attempt to invalidate any related models.
    """

    if hasattr(generated_models_cache, "delete_pattern"):
        all_versions_cache_key = all_baserow_version_table_model_cache_entry_key(
            table_id
        )
        generated_models_cache.delete_pattern(all_versions_cache_key)
    else:
        generated_models_cache.delete(table_model_cache_entry_key(table_id))


def _invalidate_all_related_models(table_id: int):
    from baserow.contrib.database.fields.registries import field_type_registry

    this_version_cache_key = table_model_cache_entry_key(table_id)
    field_attrs = generated_models_cache.get(this_version_cache_key)
    if field_attrs is not None:
        for field_obj in field_attrs.get("_field_objects", []).values():
            field = field_obj.get("field", None)
            if field is not None:
                field_type = field_type_registry.get_by_model(field)
                field_type.before_table_model_invalidated(field)

import pytest

from baserow.contrib.database.table.cache import (
    invalidate_table_in_model_cache,
    table_model_cache_version_key,
    generated_models_cache,
    clear_generated_model_cache,
    get_current_cached_model_version,
    get_cached_model_field_attrs,
)


def get_latest_attrs(table_id):
    return get_cached_model_field_attrs(
        table_id, get_current_cached_model_version(table_id)
    )


@pytest.mark.django_db
def test_changing_link_row_field_invalidates_both_tables(data_fixture):
    unrelated_table = data_fixture.create_database_table()
    table_a, table_b, link_field = data_fixture.create_two_linked_tables()
    table_a.get_model()
    table_b.get_model()
    unrelated_table.get_model()

    assert get_latest_attrs(table_a.id) is not None
    assert get_latest_attrs(table_b.id) is not None
    assert get_latest_attrs(unrelated_table.id) is not None

    link_field.save()

    assert get_latest_attrs(table_a.id) is None
    assert get_latest_attrs(table_b.id) is None
    assert get_latest_attrs(unrelated_table.id) is not None


@pytest.mark.django_db
def test_invalidating_the_cache_increments_the_version_key():
    clear_generated_model_cache()
    pretend_table_id = 1
    model_version_key = table_model_cache_version_key(pretend_table_id)
    generated_models_cache.set(model_version_key, 0, timeout=None)
    invalidate_table_in_model_cache(pretend_table_id, invalidate_related_tables=True)
    assert generated_models_cache.get(model_version_key) == 1


@pytest.mark.django_db
def test_invalidating_the_cache_if_not_cached_already_creates_v1():
    clear_generated_model_cache()
    pretend_table_id = 1
    invalidate_table_in_model_cache(pretend_table_id, invalidate_related_tables=True)
    table_version_key = table_model_cache_version_key(pretend_table_id)
    assert generated_models_cache.get(table_version_key) == 1


@pytest.mark.django_db
def test_invalidating_related_table_incrs_related_table_version_also(data_fixture):
    table_a, table_b, link_field = data_fixture.create_two_linked_tables()

    table_version_key_a = table_model_cache_version_key(table_a.id)
    table_version_key_b = table_model_cache_version_key(table_b.id)

    table_a_version = generated_models_cache.get(table_version_key_a)
    table_b_version = generated_models_cache.get(table_version_key_b)
    invalidate_table_in_model_cache(table_a.id, invalidate_related_tables=True)

    assert generated_models_cache.get(table_version_key_a) == table_a_version + 1

    assert generated_models_cache.get(table_version_key_b) == table_b_version + 1


@pytest.mark.django_db
def test_deleting_field_removes_tables_generated_model_cache_entry(data_fixture):
    field = data_fixture.create_text_field()
    field.table.get_model()

    assert get_latest_attrs(field.table_id) is not None

    field.delete()

    assert get_latest_attrs(field.table_id) is None


@pytest.mark.django_db
def test_deleting_table_removes_generated_model_cache_entry(data_fixture):
    table = data_fixture.create_database_table()
    table.get_model()

    assert get_latest_attrs(table.id) is not None

    table.delete()

    assert get_latest_attrs(table.id) is None


@pytest.mark.django_db
def test_deleting_tables_database_removes_generated_model_cache_entry(data_fixture):
    table = data_fixture.create_database_table()
    table.get_model()

    assert get_latest_attrs(table.id) is not None

    table.database.delete()

    assert get_latest_attrs(table.id) is None


@pytest.mark.django_db
def test_deleting_tables_group_removes_generated_model_cache_entry(data_fixture):
    table = data_fixture.create_database_table()
    table.get_model()

    assert get_latest_attrs(table.id) is not None

    table.database.group.delete()

    assert get_latest_attrs(table.id) is None


@pytest.mark.django_db
def test_getting_newer_version_of_stored_attrs_returns_none(data_fixture):
    table = data_fixture.create_database_table()
    table.get_model()

    current_version = get_current_cached_model_version(table.id)

    # If we are asking for the current version or an older one we will get the field
    # attrs back.
    assert get_cached_model_field_attrs(table.id, current_version) is not None
    assert get_cached_model_field_attrs(table.id, current_version - 1) is not None

    # If we are getting a newer version which doesn't exist, we'll get back None
    assert get_cached_model_field_attrs(table.id, current_version + 1) is None

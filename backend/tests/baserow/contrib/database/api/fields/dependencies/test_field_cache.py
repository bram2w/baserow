import pytest

from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.models import Field


@pytest.mark.django_db
def test_field_cache_does_no_database_lookup_for_cached_field(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    non_specific = Field.objects.get(id=field.id)
    field_cache = FieldCache()
    with django_assert_num_queries(0):
        field_cache.cache_field(field)
        specific_field = field_cache.lookup_specific(non_specific)
        field_by_name = field_cache.lookup_by_name(field.table, "field")
    assert specific_field == field
    assert field_by_name == field


@pytest.mark.django_db
def test_looking_up_non_existent_field_returns_none_after_query(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    field_cache = FieldCache()
    with django_assert_num_queries(1):
        non_existent_field = field_cache.lookup_by_name(field.table, "other field")
    assert non_existent_field is None


@pytest.mark.django_db
def test_looking_up_field_by_name_not_in_cache_queries_to_get_specific_field(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    field_cache = FieldCache()
    # 1st query = Lookup field by name
    # 2nd query = Lookup specific field
    with django_assert_num_queries(2):
        looked_up_field = field_cache.lookup_by_name(field.table, "field")
    assert looked_up_field == field

    with django_assert_num_queries(0):
        looked_up_field = field_cache.lookup_by_name(field.table, "field")
    assert looked_up_field == field


@pytest.mark.django_db
def test_looking_up_missing_specific_field_does_query(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    non_specific_field = Field.objects.get(id=field.id)
    field_cache = FieldCache()
    with django_assert_num_queries(1):
        looked_up_field = field_cache.lookup_specific(non_specific_field)
    assert looked_up_field == field

    with django_assert_num_queries(0):
        looked_up_field = field_cache.lookup_specific(non_specific_field)
    assert looked_up_field == field


@pytest.mark.django_db
def test_looking_up_specific_field_which_does_not_exist_returns_none(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    non_specific_field = Field.objects.get(id=field.id)
    field.delete()
    field_cache = FieldCache()
    with django_assert_num_queries(1):
        looked_up_field = field_cache.lookup_specific(non_specific_field)
    assert looked_up_field is None


@pytest.mark.django_db
def test_cannot_cache_trashed_field(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    field.trashed = True
    field.save()
    field_cache = FieldCache()
    with django_assert_num_queries(0):
        looked_up_field = field_cache.lookup_specific(field)
    assert looked_up_field is None


@pytest.mark.django_db
def test_field_cache_can_inherit_cache_from_another(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    non_specific = Field.objects.get(id=field.id)
    field_cache = FieldCache()
    field_cache.cache_field(field)
    with django_assert_num_queries(0):
        inherited_cache = FieldCache(existing_cache=field_cache)
        specific_field = inherited_cache.lookup_specific(non_specific)
        field_by_name = inherited_cache.lookup_by_name(field.table, "field")
    assert specific_field == field
    assert field_by_name == field


@pytest.mark.django_db
def test_field_cache_can_inherit_from_model(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    non_specific = Field.objects.get(id=field.id)
    model = field.table.get_model()
    with django_assert_num_queries(0):
        field_cache = FieldCache(existing_model=model)
        specific_field = field_cache.lookup_specific(non_specific)
        field_by_name = field_cache.lookup_by_name(field.table, "field")
        looked_up_model = field_cache.get_model(field.table)
    assert model == looked_up_model
    assert specific_field == field
    assert field_by_name == field


@pytest.mark.django_db
def test_can_add_model_with_fields_to_cache(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    non_specific = Field.objects.get(id=field.id)
    model = field.table.get_model()
    with django_assert_num_queries(0):
        field_cache = FieldCache()
        field_cache.cache_model(model)
        specific_field = field_cache.lookup_specific(non_specific)
        field_by_name = field_cache.lookup_by_name(field.table, "field")
        looked_up_model = field_cache.get_model(field.table)
    assert model == looked_up_model
    assert specific_field == field
    assert field_by_name == field


@pytest.mark.django_db
def test_can_just_add_model_fields_to_cache(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    non_specific = Field.objects.get(id=field.id)
    model = field.table.get_model()
    with django_assert_num_queries(0):
        field_cache = FieldCache()
        field_cache.cache_model_fields(model)
        specific_field = field_cache.lookup_specific(non_specific)
        field_by_name = field_cache.lookup_by_name(field.table, "field")
    assert specific_field == field
    assert field_by_name == field


@pytest.mark.django_db
def test_can_get_model_via_cache(api_client, data_fixture, django_assert_num_queries):
    field = data_fixture.create_text_field(name="field")
    # 1st query to get all fields in the table
    # 2nd query to lookup specific instance for the only field
    with django_assert_num_queries(2):
        field_cache = FieldCache()
        looked_up_model = field_cache.get_model(field.table)
    assert looked_up_model is not None
    with django_assert_num_queries(0):
        second_time_looked_up_model = field_cache.get_model(field.table)
    assert second_time_looked_up_model == looked_up_model

import pytest

from baserow.api.mixins import SearchableViewMixin


@pytest.mark.django_db
def test_searchable_view_mixin_apply_search_default(data_fixture):
    table = data_fixture.create_database_table()

    model = table.get_model()
    model.objects.create()
    model.objects.create()
    model.objects.create()

    mixin_instance = SearchableViewMixin()
    search = None
    queryset = model.objects.all()

    queryset_searched = mixin_instance.apply_search(search, queryset)

    assert queryset_searched.query == queryset.query
    assert queryset_searched.count() == 3


@pytest.mark.django_db
def test_searchable_view_mixin_apply_search(data_fixture):
    table = data_fixture.create_database_table()
    text_field = data_fixture.create_text_field(table=table)

    model = table.get_model()
    model.objects.create(**{f"field_{text_field.id}": "a"})
    model.objects.create(**{f"field_{text_field.id}": "a"})
    model.objects.create(**{f"field_{text_field.id}": "b"})

    mixin_instance = SearchableViewMixin()
    mixin_instance.search_fields = [f"field_{text_field.id}"]
    search = "a"
    queryset = model.objects.all()

    queryset_searched = mixin_instance.apply_search(search, queryset)

    assert queryset_searched.count() == 2
    assert getattr(queryset_searched[0], f"field_{text_field.id}") == "a"
    assert getattr(queryset_searched[1], f"field_{text_field.id}") == "a"


@pytest.mark.django_db
def test_searchable_view_mixin_apply_search_no_search_fields(data_fixture):
    table = data_fixture.create_database_table()
    text_field = data_fixture.create_text_field(table=table)

    model = table.get_model()
    model.objects.create(**{f"field_{text_field.id}": "a"})
    model.objects.create(**{f"field_{text_field.id}": "a"})
    model.objects.create(**{f"field_{text_field.id}": "b"})

    mixin_instance = SearchableViewMixin()

    # search should be ignored by apply_search since there aren't any search_fields
    # defined
    search = "a"
    queryset = model.objects.all()

    queryset_searched = mixin_instance.apply_search(search, queryset)

    assert queryset_searched.count() == 3

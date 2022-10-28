import pytest

from baserow.api.exceptions import (
    InvalidSortAttributeException,
    InvalidSortDirectionException,
)
from baserow.api.mixins import SortableViewMixin


@pytest.mark.django_db
def test_sortable_view_mixin_apply_sorts_or_default_sort_default(data_fixture):
    table = data_fixture.create_database_table()
    model = table.get_model()
    model.objects.create()
    model.objects.create()
    model.objects.create()

    mixin_instance = SortableViewMixin()
    sorts = None
    queryset = model.objects.all()

    queryset_sorted = mixin_instance.apply_sorts_or_default_sort(sorts, queryset)

    assert queryset_sorted.count() == 3
    assert queryset_sorted[0].id < queryset_sorted[1].id
    assert queryset_sorted[1].id < queryset_sorted[2].id


@pytest.mark.django_db
def test_sortable_view_mixin_apply_sorts_or_default_sort_key_ascending(data_fixture):
    table = data_fixture.create_database_table()
    text_field = data_fixture.create_text_field(table=table)
    model = table.get_model()
    model.objects.create(**{f"field_{text_field.id}": "c"})
    model.objects.create(**{f"field_{text_field.id}": "b"})
    model.objects.create(**{f"field_{text_field.id}": "a"})

    mixin_instance = SortableViewMixin()
    mixin_instance.sort_field_mapping = {"text_field": f"field_{text_field.id}"}
    sorts = "+text_field"
    queryset = model.objects.all()

    queryset_sorted = mixin_instance.apply_sorts_or_default_sort(sorts, queryset)

    assert queryset_sorted.count() == 3
    assert getattr(queryset_sorted[0], f"field_{text_field.id}") < getattr(
        queryset_sorted[1], f"field_{text_field.id}"
    )
    assert getattr(queryset_sorted[1], f"field_{text_field.id}") < getattr(
        queryset_sorted[2], f"field_{text_field.id}"
    )


@pytest.mark.django_db
def test_sortable_view_mixin_apply_sorts_or_default_sort_key_descending(data_fixture):
    table = data_fixture.create_database_table()
    text_field = data_fixture.create_text_field(table=table)
    model = table.get_model()
    model.objects.create(**{f"field_{text_field.id}": "c"})
    model.objects.create(**{f"field_{text_field.id}": "b"})
    model.objects.create(**{f"field_{text_field.id}": "a"})

    mixin_instance = SortableViewMixin()
    mixin_instance.sort_field_mapping = {"text_field": f"field_{text_field.id}"}
    sorts = "-text_field"
    queryset = model.objects.all()

    queryset_sorted = mixin_instance.apply_sorts_or_default_sort(sorts, queryset)

    assert queryset_sorted.count() == 3
    assert getattr(queryset_sorted[0], f"field_{text_field.id}") > getattr(
        queryset_sorted[1], f"field_{text_field.id}"
    )
    assert getattr(queryset_sorted[1], f"field_{text_field.id}") > getattr(
        queryset_sorted[2], f"field_{text_field.id}"
    )


@pytest.mark.django_db
def test_sortable_view_mixin_apply_sorts_or_default_sort_invalid_attribute(
    data_fixture,
):
    table = data_fixture.create_database_table()
    model = table.get_model()

    mixin_instance = SortableViewMixin()
    mixin_instance.sort_field_mapping = {}
    sorts = "-some_invalid_field"
    queryset = model.objects.all()

    with pytest.raises(InvalidSortAttributeException):
        mixin_instance.apply_sorts_or_default_sort("", queryset)

    with pytest.raises(InvalidSortAttributeException):
        mixin_instance.apply_sorts_or_default_sort(sorts, queryset)


@pytest.mark.django_db
def test_sortable_view_mixin_apply_sorts_or_default_sort_invalid_sort_direction(
    data_fixture,
):
    table = data_fixture.create_database_table()
    model = table.get_model()

    mixin_instance = SortableViewMixin()
    mixin_instance.sort_field_mapping = {}
    sorts = "random_string_without_direction"
    queryset = model.objects.all()

    with pytest.raises(InvalidSortDirectionException):
        mixin_instance.apply_sorts_or_default_sort(sorts, queryset)

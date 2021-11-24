import pytest
from django.conf import settings

from baserow.contrib.database.fields.dependencies.handler import FieldDependencyHandler
from baserow.contrib.database.fields.dependencies.models import (
    FieldDependency,
)
from baserow.contrib.database.fields.dependencies.circular_reference_checker import (
    will_cause_circular_dep,
)


@pytest.mark.django_db
def test_deep_circular_ref(data_fixture, django_assert_num_queries):
    depth = settings.MAX_FIELD_REFERENCE_DEPTH
    starting_field = data_fixture.create_text_field()
    previous_field = starting_field
    for i in range(depth):
        new_field = data_fixture.create_text_field(table=starting_field.table)
        FieldDependency.objects.create(dependant=previous_field, dependency=new_field)
        previous_field = new_field

    with django_assert_num_queries(1):
        assert will_cause_circular_dep(previous_field, starting_field)
    with django_assert_num_queries(1):
        assert not will_cause_circular_dep(starting_field, previous_field)


@pytest.mark.django_db
def test_get_same_table_deps(data_fixture):
    field_a = data_fixture.create_text_field()
    field_b = data_fixture.create_text_field(table=field_a.table)
    field_c = data_fixture.create_text_field(table=field_a.table)
    field_in_other_table = data_fixture.create_text_field()
    FieldDependency.objects.create(dependant=field_a, dependency=field_b)
    FieldDependency.objects.create(dependant=field_b, dependency=field_c)
    FieldDependency.objects.create(dependant=field_c, dependency=field_in_other_table)
    assert FieldDependencyHandler().get_same_table_dependencies(field_a) == [field_b]
    assert FieldDependencyHandler().get_same_table_dependencies(field_b) == [field_c]
    assert FieldDependencyHandler().get_same_table_dependencies(field_c) == []

import pytest

from baserow.contrib.database.fields.models import TextField
from baserow.contrib.database.fields.field_types import TextFieldType
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.dependencies.models import FieldDependency
from baserow.contrib.database.fields.handler import FieldDependencyHandler


@pytest.mark.django_db
def test_get_dependant_fields_with_type(data_fixture):
    table = data_fixture.create_database_table()
    text_field_1 = data_fixture.create_text_field(table=table)
    text_field_2 = data_fixture.create_text_field(table=table)
    text_field_3 = data_fixture.create_text_field(table=table)

    text_field_1_dependency_1 = data_fixture.create_text_field(table=table)
    text_field_1_dependency_2 = data_fixture.create_text_field(table=table)

    text_field_2_dependency_1 = data_fixture.create_text_field(table=table)
    text_field_2_dependency_2 = data_fixture.create_text_field(table=table)
    text_field_2_dependency_3 = data_fixture.create_text_field(table=table)

    link_row_field_via_text_field_2_and_dependency_2 = (
        data_fixture.create_link_row_field(table=table)
    )
    text_field_1_and_2_dependency_1 = data_fixture.create_text_field(table=table)

    FieldDependency.objects.create(
        dependency=text_field_1, dependant=text_field_1_dependency_1
    )
    FieldDependency.objects.create(
        dependency=text_field_1, dependant=text_field_1_dependency_2
    )
    FieldDependency.objects.create(
        dependency=text_field_1, dependant=text_field_1_and_2_dependency_1
    )

    FieldDependency.objects.create(
        dependency=text_field_2, dependant=text_field_2_dependency_1
    )
    FieldDependency.objects.create(
        dependency=text_field_2,
        dependant=text_field_2_dependency_2,
        via=link_row_field_via_text_field_2_and_dependency_2,
    )
    FieldDependency.objects.create(
        dependency=text_field_2, dependant=text_field_2_dependency_3
    )
    FieldDependency.objects.create(
        dependency=text_field_2, dependant=text_field_1_and_2_dependency_1
    )

    field_cache = FieldCache()

    results = FieldDependencyHandler.get_dependant_fields_with_type(
        field_ids=[text_field_1.id], field_cache=field_cache
    )
    assert len(results) == 3
    assert isinstance(results[0][0], TextField)
    assert isinstance(results[0][1], TextFieldType)
    assert results[0][2] is None
    assert results[0][0].id == text_field_1_dependency_1.id
    assert results[1][0].id == text_field_1_dependency_2.id
    assert results[2][0].id == text_field_1_and_2_dependency_1.id

    results = FieldDependencyHandler.get_dependant_fields_with_type(
        field_ids=[text_field_2.id], field_cache=field_cache
    )
    assert len(results) == 4
    assert results[0][0].id == text_field_2_dependency_1.id
    assert results[1][0].id == text_field_2_dependency_2.id
    assert results[1][2][0].id == link_row_field_via_text_field_2_and_dependency_2.id
    assert results[2][0].id == text_field_2_dependency_3.id
    assert results[3][0].id == text_field_1_and_2_dependency_1.id

    results = FieldDependencyHandler.get_dependant_fields_with_type(
        field_ids=[text_field_3.id], field_cache=field_cache
    )
    assert len(results) == 0

    results = FieldDependencyHandler.get_dependant_fields_with_type(
        field_ids=[text_field_1.id, text_field_2.id, text_field_3.id],
        field_cache=field_cache,
    )
    assert len(results) == 7
    assert results[0][0].id == text_field_1_dependency_1.id
    assert results[1][0].id == text_field_1_dependency_2.id
    assert results[2][0].id == text_field_1_and_2_dependency_1.id
    assert results[3][0].id == text_field_2_dependency_1.id
    assert results[4][0].id == text_field_2_dependency_2.id
    assert results[5][0].id == text_field_2_dependency_3.id
    assert results[6][0].id == text_field_1_and_2_dependency_1.id

import pytest
from rest_framework.exceptions import ValidationError

from baserow.contrib.builder.elements.models import CollectionElementField, Element
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.elements.service import ElementService


@pytest.mark.django_db
def test_create_table_element_without_fields(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page
    )

    ElementService().create_element(
        user,
        element_type_registry.get("table"),
        page=page,
        data_source_id=data_source1.id,
        fields=[],
    )

    created_element = Element.objects.last().specific

    assert created_element.data_source.id == data_source1.id


@pytest.mark.django_db
def test_create_table_element_with_fields(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page
    )

    ElementService().create_element(
        user,
        element_type_registry.get("table"),
        page=page,
        data_source_id=data_source1.id,
        fields=[
            {"name": "Field 1", "value": "get('test')"},
            {"name": "Field 2", "value": "get('test')"},
        ],
    )

    created_element = Element.objects.last().specific

    assert created_element.data_source.id == data_source1.id

    fields = list(created_element.fields.all())

    assert len(fields) == 2

    fields[0].name == "Field 1"
    fields[1].name == "Field 2"


@pytest.mark.django_db
def test_create_table_element_with_non_collection_data_source(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source2 = data_fixture.create_builder_data_source(page=page)

    with pytest.raises(ValidationError):
        ElementService().create_element(
            user,
            element_type_registry.get("table"),
            page=page,
            data_source_id=data_source1.id,
            fields=[],
        )

    assert data_source2.service is None
    with pytest.raises(ValidationError):
        ElementService().create_element(
            user,
            element_type_registry.get("table"),
            page=page,
            data_source_id=data_source2.id,
            fields=[],
        )


@pytest.mark.django_db
def test_update_table_element_without_fields(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page
    )
    table_element = data_fixture.create_builder_table_element(page=page)

    ElementService().update_element(
        user,
        table_element,
        data_source_id=data_source1.id,
    )

    table_element.refresh_from_db()

    assert table_element.data_source.id == data_source1.id

    fields = list(table_element.fields.all())

    assert len(fields) == 3

    fields[0].name == "Field 1"
    fields[1].name == "Field 2"
    fields[2].name == "Field 3"


@pytest.mark.django_db
def test_update_table_element_without_bad_data_source_type(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    table_element = data_fixture.create_builder_table_element(page=page)

    with pytest.raises(ValidationError):
        ElementService().update_element(
            user,
            table_element,
            data_source_id=data_source1.id,
        )


@pytest.mark.django_db
def test_update_table_element_with_fields(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table_element = data_fixture.create_builder_table_element(page=page)

    ElementService().update_element(
        user,
        table_element,
        fields=[
            {"name": "New field 1", "value": "get('test')"},
            {"name": "New field 2", "value": "get('test')"},
        ],
    )

    table_element.refresh_from_db()

    fields = list(table_element.fields.all())

    assert len(fields) == 2

    fields[0].name == "New field 1"
    fields[1].name == "New field 2"


@pytest.mark.django_db
def test_delete_table_element_remove_fields(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)

    table_element = data_fixture.create_builder_table_element(page=page)

    assert CollectionElementField.objects.count() == 3

    ElementService().delete_element(user, table_element)

    assert CollectionElementField.objects.count() == 0

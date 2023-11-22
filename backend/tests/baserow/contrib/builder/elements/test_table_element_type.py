import pytest
from rest_framework.exceptions import ValidationError

from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.models import CollectionField, Element
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
    )

    created_element = Element.objects.last().specific

    assert created_element.data_source.id == data_source1.id

    fields = list(created_element.fields.all())

    assert len(fields) == 3

    fields[0].name == "Column 1"


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
            {"name": "Field 1", "type": "text", "config": {"value": "get('test1')"}},
            {"name": "Field 2", "type": "text", "config": {"value": "get('test1')"}},
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
            {
                "name": "New field 1",
                "type": "text",
                "config": {"value": "get('test1')"},
            },
            {
                "name": "New field 2",
                "type": "text",
                "config": {"value": "get('test2')"},
            },
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

    assert CollectionField.objects.count() == 3

    ElementService().delete_element(user, table_element)

    assert CollectionField.objects.count() == 0


@pytest.mark.django_db
def test_duplicate_table_element_with_current_record_formulas(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)

    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
        ],
    )

    data_source1 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        table=table, page=page
    )

    table_element = data_fixture.create_builder_table_element(
        page=page,
        data_source=data_source1,
        fields=[
            {
                "name": "Field 1",
                "type": "text",
                "config": {"value": f"get('current_record.field_{fields[0].id}')"},
            },
            {
                "name": "Field 2",
                "type": "link",
                "config": {
                    "url": f"get('current_record.field_{fields[0].id}')",
                    "link_name": f"get('current_record.field_{fields[0].id}')",
                },
            },
        ],
    )

    result = ElementHandler().duplicate_element(table_element)

    assert [f.config for f in result["elements"][0].fields.all()] == [
        {"value": f"get('current_record.field_{fields[0].id}')"},
        {
            "url": f"get('current_record.field_{fields[0].id}')",
            "link_name": f"get('current_record.field_{fields[0].id}')",
        },
    ]


@pytest.mark.django_db
def test_import_table_element_with_current_record_formulas_with_update(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)

    table, fields, _ = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
        ],
    )

    data_source1 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        table=table, page=page
    )

    IMPORT_REF = {
        "id": 42,
        "order": "1.00000000000000000000",
        "type": "table",
        "parent_element_id": None,
        "place_in_container": None,
        "style_padding_top": 10,
        "style_padding_bottom": 10,
        "data_source_id": 42,
        "items_per_page": 20,
        "fields": [
            {
                "name": "Field 1",
                "config": {"value": f"get('current_record.field_42')"},
                "type": "text",
            },
            {
                "name": "Field 2",
                "config": {
                    "url": f"get('current_record.field_42')",
                    "link_name": f"get('current_record.field_42')",
                },
                "type": "link",
            },
        ],
    }

    id_mapping = {
        "database_fields": {42: fields[0].id},
        "builder_data_sources": {42: data_source1.id},
    }

    ElementHandler().import_element(page, IMPORT_REF, id_mapping)

    [imported_table_element] = page.element_set.all()

    assert imported_table_element.specific.data_source_id == data_source1.id

    assert [f.config for f in imported_table_element.specific.fields.all()] == [
        {"value": f"get('current_record.field_{fields[0].id}')"},
        {
            "url": f"get('current_record.field_{fields[0].id}')",
            "link_name": f"get('current_record.field_{fields[0].id}')",
        },
    ]

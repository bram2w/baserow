import pytest

from baserow.contrib.builder.elements.collection_field_types import (
    TagsCollectionFieldType,
)
from baserow.contrib.builder.pages.service import PageService


@pytest.mark.django_db
def test_import_export_tags_collection_field_type(data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("Color", "text"),
        ],
        rows=[
            ["BMW", "#ffffff"],
        ],
    )
    name_field, color_field = fields
    data_source = data_fixture.create_builder_local_baserow_list_rows_data_source(
        table=table, page=page
    )
    table_element = data_fixture.create_builder_table_element(
        page=page,
        data_source=data_source,
        fields=[
            {
                "name": "Colors as formula",
                "type": "tags",
                "config": {
                    "values": f"get('data_source.{data_source.id}.0.{name_field.db_column}')",
                    "colors": f"get('data_source.{data_source.id}.0.{color_field.db_column}')",
                    "colors_is_formula": True,
                },
            },
            {
                "name": "Colors as hex",
                "type": "tags",
                "config": {
                    "values": "'a,b,c'",
                    "colors": "#d06060ff",
                    "colors_is_formula": False,
                },
            },
        ],
    )

    duplicated_page = PageService().duplicate_page(user, page)
    data_source2 = duplicated_page.datasource_set.first()

    id_mapping = {"builder_data_sources": {data_source.id: data_source2.id}}

    tags_with_formula = table_element.fields.get(name="Colors as formula")
    exported_with = TagsCollectionFieldType().export_serialized(tags_with_formula)
    imported_with = TagsCollectionFieldType().import_serialized(
        exported_with, id_mapping, data_source.id
    )

    assert imported_with.config == {
        "values": f"get('data_source.{data_source2.id}.0.{name_field.db_column}')",
        "colors": f"get('data_source.{data_source2.id}.0.{color_field.db_column}')",
        "colors_is_formula": True,
    }

    tags_without_formula = table_element.fields.get(name="Colors as hex")
    exported_without = TagsCollectionFieldType().export_serialized(tags_without_formula)
    imported_with = TagsCollectionFieldType().import_serialized(
        exported_without, id_mapping, data_source.id
    )

    assert imported_with.config == {
        "values": "'a,b,c'",
        "colors_is_formula": False,
        "colors": "#d06060ff",
    }

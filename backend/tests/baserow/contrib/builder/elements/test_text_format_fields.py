"""
Export/import tests for the Markdown text format of the form element labels,
the choice element option names, the collection field names and the text
collection field values. The format is stored inside the value itself, as a
`__markdown__` marker in front of it, so there is no separate property to carry.
"""

from collections import defaultdict

import pytest

from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.pages.service import PageService
from baserow.core.formula import BaserowFormulaObject
from baserow.core.formula.field import BASEROW_FORMULA_VERSION_INITIAL
from baserow.core.formula.text_format import MARKDOWN_PREFIX
from baserow.core.formula.types import BASEROW_FORMULA_MODE_SIMPLE
from baserow.core.utils import MirrorDict

# The element types with a Markdown-capable `label`.
LABEL_ELEMENT_TYPES = [
    "input_text",
    "choice",
    "checkbox",
    "rating_input",
    "datetime_picker",
    "record_selector",
]


@pytest.fixture
def data_source_pair(data_fixture):
    """
    A page with a list rows data source, and a duplicated page whose data
    source has a different id, to check that `get()` paths are rewritten.
    """

    user, _ = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    table, fields, _ = data_fixture.build_table(
        user=user, columns=[("Name", "text")], rows=[["Foo"]]
    )
    data_source = data_fixture.create_builder_local_baserow_list_rows_data_source(
        table=table, page=page
    )
    duplicated_page = PageService().duplicate_page(user, page)
    data_source2 = duplicated_page.datasource_set.first()

    return {
        "user": user,
        "page": page,
        "field": fields[0],
        "data_source": data_source,
        "data_source2": data_source2,
        "id_mapping": {"builder_data_sources": {data_source.id: data_source2.id}},
    }


@pytest.mark.django_db
@pytest.mark.parametrize("element_type_name", LABEL_ELEMENT_TYPES)
def test_export_import_element_markdown_label(
    data_fixture, data_source_pair, element_type_name
):
    """
    The marker survives an export/import and the `get()` path behind it is
    rewritten like any other formula.
    """

    element_type = element_type_registry.get(element_type_name)
    data_source = data_source_pair["data_source"]
    data_source2 = data_source_pair["data_source2"]
    db_column = data_source_pair["field"].db_column
    element = data_fixture.create_builder_element(
        type(element_type),
        data_source_pair["user"],
        page=data_source_pair["page"],
        label=f"{MARKDOWN_PREFIX}get('data_source.{data_source.id}.0.{db_column}')",
    )

    exported = element_type.export_serialized(element)
    assert exported["label"]["formula"] == (
        f"{MARKDOWN_PREFIX}get('data_source.{data_source.id}.0.{db_column}')"
    )

    imported_element = ElementHandler().import_element(
        data_source_pair["page"], exported, data_source_pair["id_mapping"]
    )

    assert imported_element.id != element.id
    assert imported_element.label == BaserowFormulaObject(
        formula=f"{MARKDOWN_PREFIX}get('data_source.{data_source2.id}.0.{db_column}')",
        version=BASEROW_FORMULA_VERSION_INITIAL,
        mode=BASEROW_FORMULA_MODE_SIMPLE,
    )


@pytest.mark.django_db
def test_export_import_choice_element_markdown_option_names(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    element = data_fixture.create_builder_choice_element(user=user, page=page)
    element.choiceelementoption_set.create(value=None, name=f"{MARKDOWN_PREFIX}**a**")
    element.choiceelementoption_set.create(value="b", name="plain b")
    element_type = element.get_type()

    exported = element_type.export_serialized(element)
    assert [option["name"] for option in exported["options"]] == [
        f"{MARKDOWN_PREFIX}**a**",
        "plain b",
    ]

    id_mapping = defaultdict(lambda: MirrorDict())
    imported_element = ElementHandler().import_element(page, exported, id_mapping)

    assert list(
        imported_element.choiceelementoption_set.values_list("value", "name")
    ) == [(None, f"{MARKDOWN_PREFIX}**a**"), ("b", "plain b")]


@pytest.mark.django_db
def test_export_import_collection_field_markdown_name(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table_element = data_fixture.create_builder_table_element(
        user=user,
        page=page,
        fields=[
            {
                "name": f"{MARKDOWN_PREFIX}**Bold** header",
                "type": "text",
                "config": {"value": "'x'"},
            },
            {"name": "Plain header", "type": "text", "config": {"value": "'y'"}},
        ],
    )

    exported = table_element.get_type().export_serialized(table_element)
    assert exported["fields"][0]["name"] == f"{MARKDOWN_PREFIX}**Bold** header"
    assert exported["fields"][1]["name"] == "Plain header"

    id_mapping = defaultdict(lambda: MirrorDict())
    imported_table_element = ElementHandler().import_element(page, exported, id_mapping)

    markdown_field, plain_field = imported_table_element.fields.all()
    assert markdown_field.name == f"{MARKDOWN_PREFIX}**Bold** header"
    assert plain_field.name == "Plain header"


@pytest.mark.django_db
def test_export_import_text_collection_field_markdown_value(
    data_fixture, data_source_pair
):
    """
    The text collection field value lives in the JSON `config`, and is imported
    through the same formula importer as the element formulas.
    """

    data_source = data_source_pair["data_source"]
    data_source2 = data_source_pair["data_source2"]
    db_column = data_source_pair["field"].db_column
    table_element = data_fixture.create_builder_table_element(
        page=data_source_pair["page"],
        data_source=data_source,
        fields=[
            {
                "name": "Foo Field",
                "type": "text",
                "config": {
                    "value": f"{MARKDOWN_PREFIX}get('data_source.{data_source.id}.0.{db_column}')"
                },
            },
        ],
    )

    exported = table_element.get_type().export_serialized(table_element)
    imported_table_element = ElementHandler().import_element(
        data_source_pair["page"], exported, data_source_pair["id_mapping"]
    )

    imported_field = imported_table_element.fields.get(name="Foo Field")
    assert imported_field.config == {
        "value": BaserowFormulaObject(
            formula=f"{MARKDOWN_PREFIX}get('data_source.{data_source2.id}.0.{db_column}')",
            version=BASEROW_FORMULA_VERSION_INITIAL,
            mode=BASEROW_FORMULA_MODE_SIMPLE,
        )
    }

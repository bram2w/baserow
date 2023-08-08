import pytest

from baserow.contrib.builder.application_types import BuilderApplicationType
from baserow.contrib.builder.elements.models import (
    ColumnElement,
    Element,
    HeadingElement,
    ParagraphElement,
)
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.pages.models import Page
from baserow.core.db import specific_iterator
from baserow.core.registries import ImportExportConfig
from baserow.core.trash.handler import TrashHandler


@pytest.mark.django_db
def test_builder_application_type_init_application(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)

    assert Page.objects.count() == 0

    BuilderApplicationType().init_application(user, builder)

    assert Page.objects.count() == 1


@pytest.mark.django_db
def test_builder_application_export(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)

    page1 = data_fixture.create_builder_page(builder=builder)
    page2 = data_fixture.create_builder_page(builder=builder)

    element1 = data_fixture.create_builder_heading_element(
        page=page1, level=2, value="foo"
    )
    element2 = data_fixture.create_builder_paragraph_element(page=page1)
    element3 = data_fixture.create_builder_heading_element(page=page2)
    element_container = data_fixture.create_builder_column_element(
        page=page1, column_amount=3, column_gap=50
    )
    element_inside_container = data_fixture.create_builder_paragraph_element(
        page=page1, parent_element=element_container, place_in_container="0"
    )

    integration = data_fixture.create_local_baserow_integration(
        application=builder, authorized_user=user, name="test"
    )

    datasource1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page1, user=user, name="source 1", integration=integration
    )
    datasource2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page2, user=user, name="source 2", integration=integration
    )
    datasource3 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page2, user=user, name="source 3", integration=integration
    )

    serialized = BuilderApplicationType().export_serialized(
        builder, ImportExportConfig(include_permission_data=True)
    )

    assert serialized == {
        "pages": [
            {
                "id": page1.id,
                "name": page1.name,
                "order": page1.order,
                "path": page1.path,
                "path_params": page1.path_params,
                "data_sources": [
                    {
                        "id": datasource1.id,
                        "name": "source 1",
                        "order": "1.00000000000000000000",
                        "service": {
                            "id": datasource1.service.id,
                            "integration_id": integration.id,
                            "row_id": "",
                            "table_id": None,
                            "type": "local_baserow_get_row",
                        },
                    },
                ],
                "elements": [
                    {
                        "id": element1.id,
                        "type": "heading",
                        "order": str(element1.order),
                        "parent_element_id": None,
                        "place_in_container": None,
                        "style_padding_top": 10,
                        "style_padding_bottom": 10,
                        "value": element1.value,
                        "level": element1.level,
                    },
                    {
                        "id": element2.id,
                        "type": "paragraph",
                        "order": str(element2.order),
                        "parent_element_id": None,
                        "place_in_container": None,
                        "style_padding_top": 10,
                        "style_padding_bottom": 10,
                        "value": element2.value,
                    },
                    {
                        "id": element_container.id,
                        "type": "column",
                        "parent_element_id": None,
                        "place_in_container": None,
                        "style_padding_top": 10,
                        "style_padding_bottom": 10,
                        "order": str(element_container.order),
                        "column_amount": 3,
                        "column_gap": 50,
                        "alignment": "top",
                    },
                    {
                        "id": element_inside_container.id,
                        "type": "paragraph",
                        "parent_element_id": element_container.id,
                        "place_in_container": "0",
                        "style_padding_top": 10,
                        "style_padding_bottom": 10,
                        "order": str(element_inside_container.order),
                        "value": element_inside_container.value,
                    },
                ],
            },
            {
                "id": page2.id,
                "name": page2.name,
                "order": page2.order,
                "path": page2.path,
                "path_params": page2.path_params,
                "data_sources": [
                    {
                        "id": datasource2.id,
                        "name": "source 2",
                        "order": "1.00000000000000000000",
                        "service": {
                            "id": datasource2.service.id,
                            "integration_id": integration.id,
                            "row_id": "",
                            "table_id": None,
                            "type": "local_baserow_get_row",
                        },
                    },
                    {
                        "id": datasource3.id,
                        "name": "source 3",
                        "order": "2.00000000000000000000",
                        "service": {
                            "id": datasource3.service.id,
                            "integration_id": integration.id,
                            "table_id": None,
                            "type": "local_baserow_list_rows",
                        },
                    },
                ],
                "elements": [
                    {
                        "id": element3.id,
                        "type": "heading",
                        "order": str(element3.order),
                        "parent_element_id": None,
                        "place_in_container": None,
                        "style_padding_top": 10,
                        "style_padding_bottom": 10,
                        "value": element3.value,
                        "level": element3.level,
                    },
                ],
            },
        ],
        "integrations": [
            {
                "authorized_user_username": user.username,
                "id": integration.id,
                "name": "test",
                "order": "1.00000000000000000000",
                "type": "local_baserow",
            },
        ],
        "id": builder.id,
        "name": builder.name,
        "order": builder.order,
        "type": "builder",
    }


IMPORT_REFERENCE = {
    "pages": [
        {
            "id": 999,
            "name": "Tammy Hall",
            "order": 1,
            "path": "/test",
            "path_params": {},
            "elements": [
                {
                    "id": 998,
                    "type": "heading",
                    "parent_element_id": None,
                    "place_in_container": None,
                    "order": 1,
                    "value": "foo",
                    "level": 2,
                },
                {
                    "id": 999,
                    "type": "paragraph",
                    "parent_element_id": None,
                    "place_in_container": None,
                    "order": 2,
                    "value": "",
                },
                {
                    "id": 500,
                    "type": "column",
                    "parent_element_id": None,
                    "place_in_container": None,
                    "style_padding_top": 10,
                    "style_padding_bottom": 10,
                    "order": 3,
                    "column_amount": 3,
                    "column_gap": 50,
                    "alignment": "top",
                },
                {
                    "id": 501,
                    "type": "paragraph",
                    "parent_element_id": 500,
                    "place_in_container": "0",
                    "style_padding_top": 10,
                    "style_padding_bottom": 10,
                    "order": 1,
                    "value": "test",
                },
            ],
            "data_sources": [
                {
                    "id": 4,
                    "name": "source 0",
                    "order": "1.00000000000000000000",
                    "service": None,
                },
                {
                    "id": 5,
                    "name": "source 1",
                    "order": "2.00000000000000000000",
                    "service": {
                        "id": 17,
                        "integration_id": None,
                        "table_id": None,
                        "type": "local_baserow_list_rows",
                    },
                },
            ],
        },
        {
            "id": 998,
            "name": "Megan Clark",
            "order": 2,
            "path": "/test2",
            "path_params": {},
            "elements": [
                {
                    "id": 997,
                    "type": "heading",
                    "parent_element_id": None,
                    "place_in_container": None,
                    "order": 1,
                    "value": "",
                    "level": 1,
                }
            ],
            "data_sources": [
                {
                    "id": 1,
                    "name": "source 2",
                    "order": "1.00000000000000000000",
                    "service": {
                        "id": 1,
                        "integration_id": 42,
                        "row_id": "",
                        "table_id": None,
                        "type": "local_baserow_get_row",
                    },
                },
                {
                    "id": 3,
                    "name": "source 3",
                    "order": "2.00000000000000000000",
                    "service": {
                        "id": 2,
                        "integration_id": 42,
                        "table_id": None,
                        "type": "local_baserow_list_rows",
                    },
                },
            ],
        },
    ],
    "integrations": [
        {
            "authorized_user_username": "test@baserow.io",
            "id": 42,
            "name": "test",
            "order": "1.00000000000000000000",
            "type": "local_baserow",
        },
    ],
    "id": 999,
    "name": "Holly Sherman",
    "order": 0,
    "type": "builder",
}


@pytest.mark.django_db
def test_builder_application_import(data_fixture):
    user = data_fixture.create_user(email="test@baserow.io")
    workspace = data_fixture.create_workspace(user=user)

    config = ImportExportConfig(include_permission_data=True)
    builder = BuilderApplicationType().import_serialized(
        workspace, IMPORT_REFERENCE, config, {}
    )

    assert builder.id != IMPORT_REFERENCE["id"]
    assert builder.page_set.count() == 2

    assert builder.integrations.count() == 1
    first_integration = builder.integrations.first().specific
    assert first_integration.authorized_user.id == user.id

    [page1, page2] = builder.page_set.all()

    assert page1.element_set.count() == 4
    assert page2.element_set.count() == 1

    assert page1.datasource_set.count() == 2
    assert page2.datasource_set.count() == 2

    first_data_source = page2.datasource_set.first()
    assert first_data_source.name == "source 2"
    assert first_data_source.service.integration.id == first_integration.id

    [
        element1,
        element_inside_container,
        element2,
        container_element,
    ] = specific_iterator(page1.element_set.all())

    assert isinstance(element1, HeadingElement)
    assert isinstance(element2, ParagraphElement)
    assert isinstance(container_element, ColumnElement)

    assert element1.order == 1
    assert element1.level == 2

    assert element_inside_container.parent_element.specific == container_element


@pytest.mark.django_db
def test_delete_builder_application_with_published_builder(data_fixture):
    builder = data_fixture.create_builder_application()
    builder_to = data_fixture.create_builder_application(workspace=None)
    domain1 = data_fixture.create_builder_domain(
        builder=builder, published_to=builder_to
    )

    TrashHandler.permanently_delete(builder)

    assert Builder.objects.count() == 0


@pytest.mark.django_db
def test_import_element(data_fixture):
    element = data_fixture.create_builder_paragraph_element(value="test")
    element_type = element_type_registry.get_by_model(element)
    element_serialized = element_type.export_serialized(element)
    serialized_page = {
        "_object": element.page,
        "_element_objects": [],
        "elements": [element_serialized],
    }

    element_imported = BuilderApplicationType().import_element(
        element_serialized,
        serialized_page,
        {"builder_page_elements": {}},
    )

    assert element_imported.id != element.id
    assert element_imported.specific.value == element.value


@pytest.mark.django_db
def test_import_element_has_to_import_parent_first(data_fixture):
    page = data_fixture.create_builder_page()
    parent = data_fixture.create_builder_column_element(page=page, column_amount=15)
    element = data_fixture.create_builder_paragraph_element(
        page=page, parent_element=parent
    )
    parent_serialized = element_type_registry.get_by_model(parent).export_serialized(
        parent
    )
    element_serialized = element_type_registry.get_by_model(element).export_serialized(
        element
    )
    serialized_page = {
        "_object": page,
        "_element_objects": [],
        "elements": [parent_serialized, element_serialized],
    }

    element_imported = BuilderApplicationType().import_element(
        element_serialized,
        serialized_page,
        {"builder_page_elements": {}},
    )

    assert element_imported.id != element.id
    assert element_imported.specific.value == element.value

    parent_imported = Element.objects.get(id=element_imported.parent_element_id)

    assert parent_imported.id != parent.id
    assert parent_imported.specific.column_amount == parent.column_amount


@pytest.mark.django_db
def test_import_element_has_to_instance_already_created(data_fixture):
    element = data_fixture.create_builder_paragraph_element()
    element_imported = data_fixture.create_builder_paragraph_element()
    element_serialized = element_type_registry.get_by_model(element).export_serialized(
        element
    )
    serialized_page = {
        "_object": element_imported.page,
        "_element_objects": [element_imported],
        "elements": [element_serialized],
    }

    element_returned = BuilderApplicationType().import_element(
        element_serialized,
        serialized_page,
        {"builder_page_elements": {element.id: element_imported.id}},
    )

    assert element_returned is element_imported
    assert Element.objects.count() == 2

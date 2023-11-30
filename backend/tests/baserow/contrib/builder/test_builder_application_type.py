import pytest

from baserow.contrib.builder.application_types import BuilderApplicationType
from baserow.contrib.builder.elements.models import (
    ColumnElement,
    HeadingElement,
    ParagraphElement,
    TableElement,
)
from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.workflow_actions.handler import (
    BuilderWorkflowActionHandler,
)
from baserow.contrib.builder.workflow_actions.models import EventTypes
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

    user_source = data_fixture.create_user_source_with_first_type(
        application=builder, user=user, integration=integration
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

    element4 = data_fixture.create_builder_table_element(
        page=page2, data_source=datasource3, items_per_page=42
    )

    workflow_action_1 = data_fixture.create_notification_workflow_action(
        page=page1,
        element=element1,
        event=EventTypes.CLICK,
        description="hello",
        title="there",
    )

    serialized = BuilderApplicationType().export_serialized(
        builder, ImportExportConfig(include_permission_data=True)
    )

    reference = {
        "pages": [
            {
                "id": page1.id,
                "name": page1.name,
                "order": page1.order,
                "path": page1.path,
                "path_params": page1.path_params,
                "workflow_actions": [
                    {
                        "id": workflow_action_1.id,
                        "type": "notification",
                        "element_id": element1.id,
                        "event": EventTypes.CLICK.value,
                        "page_id": page1.id,
                        "description": "hello",
                        "title": "there",
                    }
                ],
                "data_sources": [
                    {
                        "id": datasource1.id,
                        "name": "source 1",
                        "order": "1.00000000000000000000",
                        "service": {
                            "id": datasource1.service.id,
                            "integration_id": integration.id,
                            "filters": [],
                            "row_id": "",
                            "view_id": None,
                            "table_id": None,
                            "search_query": "",
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
                        "style_background_color": "#ffffffff",
                        "style_border_bottom_color": "border",
                        "style_border_bottom_size": 0,
                        "style_border_top_color": "border",
                        "style_border_top_size": 0,
                        "style_width": "normal",
                        "style_padding_top": 10,
                        "style_padding_bottom": 10,
                        "style_background": "none",
                        "value": element1.value,
                        "level": element1.level,
                    },
                    {
                        "id": element2.id,
                        "type": "paragraph",
                        "order": str(element2.order),
                        "parent_element_id": None,
                        "place_in_container": None,
                        "style_background_color": "#ffffffff",
                        "style_border_bottom_color": "border",
                        "style_border_bottom_size": 0,
                        "style_border_top_color": "border",
                        "style_border_top_size": 0,
                        "style_width": "normal",
                        "style_padding_top": 10,
                        "style_padding_bottom": 10,
                        "style_background": "none",
                        "value": element2.value,
                    },
                    {
                        "id": element_container.id,
                        "type": "column",
                        "parent_element_id": None,
                        "place_in_container": None,
                        "style_background_color": "#ffffffff",
                        "style_border_bottom_color": "border",
                        "style_border_bottom_size": 0,
                        "style_border_top_color": "border",
                        "style_border_top_size": 0,
                        "style_width": "normal",
                        "style_padding_top": 10,
                        "style_padding_bottom": 10,
                        "style_background": "none",
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
                        "style_background_color": "#ffffffff",
                        "style_border_bottom_color": "border",
                        "style_border_bottom_size": 0,
                        "style_border_top_color": "border",
                        "style_border_top_size": 0,
                        "style_width": "normal",
                        "style_padding_top": 10,
                        "style_padding_bottom": 10,
                        "style_background": "none",
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
                "workflow_actions": [],
                "data_sources": [
                    {
                        "id": datasource2.id,
                        "name": "source 2",
                        "order": "1.00000000000000000000",
                        "service": {
                            "id": datasource2.service.id,
                            "integration_id": integration.id,
                            "filters": [],
                            "row_id": "",
                            "view_id": None,
                            "table_id": None,
                            "search_query": "",
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
                            "filters": [],
                            "sortings": [],
                            "view_id": None,
                            "table_id": None,
                            "search_query": "",
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
                        "style_background_color": "#ffffffff",
                        "style_border_bottom_color": "border",
                        "style_border_bottom_size": 0,
                        "style_border_top_color": "border",
                        "style_border_top_size": 0,
                        "style_width": "normal",
                        "style_padding_top": 10,
                        "style_padding_bottom": 10,
                        "style_background": "none",
                        "value": element3.value,
                        "level": element3.level,
                    },
                    {
                        "id": element4.id,
                        "type": "table",
                        "order": str(element4.order),
                        "parent_element_id": None,
                        "place_in_container": None,
                        "style_background_color": "#ffffffff",
                        "style_border_bottom_color": "border",
                        "style_border_bottom_size": 0,
                        "style_border_top_color": "border",
                        "style_border_top_size": 0,
                        "style_width": "normal",
                        "style_padding_top": 10,
                        "style_padding_bottom": 10,
                        "style_background": "none",
                        "items_per_page": 42,
                        "data_source_id": element4.data_source.id,
                        "fields": [
                            {"name": f.name, "type": f.type, "config": f.config}
                            for f in element4.fields.all()
                        ],
                    },
                ],
            },
        ],
        "integrations": [
            {
                "authorized_user": user.username,
                "id": integration.id,
                "name": "test",
                "order": "1.00000000000000000000",
                "type": "local_baserow",
            },
        ],
        "user_sources": [
            {
                "email_field_id": None,
                "id": user_source.id,
                "integration_id": integration.id,
                "name": "",
                "name_field_id": None,
                "order": "1.00000000000000000000",
                "table_id": None,
                "type": "local_baserow",
            },
        ],
        "theme": {
            "heading_1_color": "#000000ff",
            "heading_1_font_size": 24,
            "heading_2_color": "#000000ff",
            "heading_2_font_size": 20,
            "heading_3_color": "#000000ff",
            "heading_3_font_size": 16,
            "primary_color": "#000000ff",
            "secondary_color": "#000000ff",
            "border_color": "#d3d3d3ff",
        },
        "id": builder.id,
        "name": builder.name,
        "order": builder.order,
        "type": "builder",
    }

    assert serialized == reference


IMPORT_REFERENCE = {
    "pages": [
        {
            "id": 999,
            "name": "Tammy Hall",
            "order": 1,
            "path": "/test",
            "path_params": {},
            "workflow_actions": [
                {
                    "id": 123,
                    "page_id": 999,
                    "element_id": 998,
                    "type": "notification",
                    "description": "'hello'",
                    "title": "'there'",
                }
            ],
            "elements": [
                {
                    "id": 998,
                    "type": "heading",
                    "parent_element_id": None,
                    "place_in_container": None,
                    "style_background": "none",
                    "style_background_color": "#ffffffff",
                    "style_border_bottom_color": "border",
                    "style_border_bottom_size": 0,
                    "style_border_top_color": "border",
                    "style_border_top_size": 0,
                    "style_width": "normal",
                    "order": 1,
                    "value": "'foo'",
                    "level": 2,
                },
                {
                    "id": 999,
                    "type": "paragraph",
                    "parent_element_id": None,
                    "place_in_container": None,
                    "style_background": "none",
                    "style_background_color": "#ffffffff",
                    "style_border_bottom_color": "border",
                    "style_border_bottom_size": 0,
                    "style_border_top_color": "border",
                    "style_border_top_size": 0,
                    "style_width": "normal",
                    "order": 2,
                    "value": "",
                },
                {
                    "id": 1000,
                    "type": "table",
                    "parent_element_id": None,
                    "place_in_container": None,
                    "style_background": "none",
                    "style_background_color": "#ffffffff",
                    "style_border_bottom_color": "border",
                    "style_border_bottom_size": 0,
                    "style_border_top_color": "border",
                    "style_border_top_size": 0,
                    "style_width": "normal",
                    "items_per_page": 42,
                    "order": 2.5,
                    "data_source_id": 5,
                    "fields": [
                        {
                            "name": "F 1",
                            "type": "text",
                            "config": {"value": "get('current_record.field_25')"},
                        },
                        {
                            "name": "F 2",
                            "type": "link",
                            "config": {
                                "url": "get('current_record.field_25')",
                                "link_name": "'Test'",
                            },
                        },
                    ],
                },
                {
                    "id": 502,
                    "type": "paragraph",
                    "parent_element_id": 500,
                    "place_in_container": "1",
                    "style_background": "none",
                    "style_background_color": "#ffffffff",
                    "style_border_bottom_color": "border",
                    "style_border_bottom_size": 0,
                    "style_border_top_color": "border",
                    "style_border_top_size": 0,
                    "style_width": "normal",
                    "style_padding_top": 10,
                    "style_padding_bottom": 10,
                    "order": 1.5,
                    "value": "'test'",
                },
                {
                    "id": 500,
                    "type": "column",
                    "parent_element_id": None,
                    "place_in_container": None,
                    "style_background": "none",
                    "style_background_color": "#ffffffff",
                    "style_border_bottom_color": "border",
                    "style_border_bottom_size": 0,
                    "style_border_top_color": "border",
                    "style_border_top_size": 0,
                    "style_width": "normal",
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
                    "style_background": "none",
                    "style_background_color": "#ffffffff",
                    "style_border_bottom_color": "border",
                    "style_border_bottom_size": 0,
                    "style_border_top_color": "border",
                    "style_border_top_size": 0,
                    "style_width": "normal",
                    "style_padding_top": 10,
                    "style_padding_bottom": 10,
                    "order": 1,
                    "value": "'test'",
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
                        "view_id": None,
                        "table_id": None,
                        "search_query": "",
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
            "workflow_actions": [],
            "elements": [
                {
                    "id": 997,
                    "type": "heading",
                    "parent_element_id": None,
                    "place_in_container": None,
                    "style_background": "none",
                    "style_background_color": "#ffffffff",
                    "style_border_bottom_color": "border",
                    "style_border_bottom_size": 0,
                    "style_border_top_color": "border",
                    "style_border_top_size": 0,
                    "style_width": "normal",
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
                        "view_id": None,
                        "table_id": None,
                        "search_query": "",
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
                        "view_id": None,
                        "table_id": None,
                        "search_query": "",
                        "type": "local_baserow_list_rows",
                    },
                },
            ],
        },
    ],
    "integrations": [
        {
            "authorized_user": "test@baserow.io",
            "id": 42,
            "name": "test",
            "order": "1.00000000000000000000",
            "type": "local_baserow",
        },
    ],
    "user_sources": [
        {
            "email_field_id": None,
            "id": 42,
            "integration_id": 42,
            "name": "My user source",
            "name_field_id": None,
            "order": "1.00000000000000000000",
            "table_id": None,
            "type": "local_baserow",
        },
    ],
    "theme": {
        "heading_1_color": "#f00000ff",
        "heading_1_font_size": 25,
        "heading_2_color": "#f00000ff",
        "heading_2_font_size": 21,
        "heading_3_color": "#f00000ff",
        "heading_3_font_size": 17,
        "primary_color": "#f00000ff",
        "secondary_color": "#f00000ff",
    },
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

    assert builder.user_sources.count() == 1

    [page1, page2] = builder.page_set.all()

    assert page1.element_set.count() == 6
    assert page2.element_set.count() == 1

    assert page1.datasource_set.count() == 2
    assert page2.datasource_set.count() == 2

    first_data_source = page2.datasource_set.first()
    assert first_data_source.name == "source 2"
    assert first_data_source.service.integration.id == first_integration.id

    theme_config_block = builder.mainthemeconfigblock
    assert theme_config_block.heading_1_color == "#f00000ff"
    assert theme_config_block.heading_1_font_size == 25
    assert theme_config_block.heading_2_color == "#f00000ff"
    assert theme_config_block.heading_2_font_size == 21
    assert theme_config_block.heading_3_color == "#f00000ff"
    assert theme_config_block.heading_3_font_size == 17
    assert theme_config_block.primary_color == "#f00000ff"
    assert theme_config_block.secondary_color == "#f00000ff"

    [
        element1,
        element_inside_container,
        element_inside_container2,
        element2,
        table_element,
        container_element,
    ] = specific_iterator(page1.element_set.all())

    assert isinstance(element1, HeadingElement)
    assert isinstance(element2, ParagraphElement)
    assert isinstance(container_element, ColumnElement)
    assert isinstance(table_element, TableElement)

    assert table_element.fields.count() == 2
    assert table_element.items_per_page == 42

    assert element1.order == 1
    assert element1.level == 2

    assert element_inside_container.parent_element.specific == container_element
    assert element_inside_container2.parent_element.specific == container_element

    [workflow_action] = BuilderWorkflowActionHandler().get_workflow_actions(page1)

    assert workflow_action.element_id == element1.id
    assert workflow_action.description == "'hello'"
    assert workflow_action.title == "'there'"


@pytest.mark.django_db
def test_delete_builder_application_with_published_builder(data_fixture):
    builder = data_fixture.create_builder_application()
    builder_to = data_fixture.create_builder_application(workspace=None)
    domain1 = data_fixture.create_builder_custom_domain(
        builder=builder, published_to=builder_to
    )

    TrashHandler.permanently_delete(builder)

    assert Builder.objects.count() == 0

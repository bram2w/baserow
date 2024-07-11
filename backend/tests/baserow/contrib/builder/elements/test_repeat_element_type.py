from collections import defaultdict

import pytest

from baserow.contrib.builder.elements.models import (
    ButtonElement,
    Element,
    HeadingElement,
    LinkElement,
)
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.workflow_actions.models import NotificationWorkflowAction
from baserow.core.utils import MirrorDict


@pytest.mark.django_db
def test_repeat_element_import_child_with_formula_with_current_record(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)

    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
        ],
    )

    field = fields[0]

    integration = data_fixture.create_local_baserow_integration(
        application=builder, authorized_user=user
    )

    exported = {
        "id": 5,
        "name": "Page",
        "order": 8,
        "path": "/page",
        "path_params": [],
        "elements": [
            {
                "id": 23,
                "order": "1.00000000000000000000",
                "type": "repeat",
                "parent_element_id": None,
                "place_in_container": None,
                "visibility": "all",
                "data_source_id": 3,
                "items_per_page": 20,
                "orientation": "vertical",
                "items_per_row": {"tablet": 2, "desktop": 2, "smartphone": 2},
                "roles": [],
                "role_type": Element.ROLE_TYPES.ALLOW_ALL,
            },
            {
                "id": 24,
                "order": "1.00000000000000000000",
                "type": "column",
                "parent_element_id": 23,
                "place_in_container": None,
                "visibility": "all",
                "column_amount": 3,
                "column_gap": 20,
                "alignment": "top",
                "roles": [],
                "role_type": Element.ROLE_TYPES.ALLOW_ALL,
            },
            {
                "id": 29,
                "order": "1.00000000000000000000",
                "type": "button",
                "parent_element_id": 24,
                "place_in_container": "0",
                "visibility": "all",
                "value": "get('current_record.field_424')",
                "width": "auto",
                "alignment": "left",
                "button_color": "primary",
                "roles": [],
                "role_type": Element.ROLE_TYPES.ALLOW_ALL,
            },
            {
                "id": 290,
                "order": "2.00000000000000000000",
                "type": "heading",
                "parent_element_id": 24,
                "place_in_container": "0",
                "visibility": "all",
                "value": "get('current_record.field_424')",
                "roles": [],
                "role_type": Element.ROLE_TYPES.ALLOW_ALL,
            },
            {
                "id": 291,
                "order": "3.00000000000000000000",
                "type": "link",
                "parent_element_id": 24,
                "place_in_container": "0",
                "visibility": "all",
                "value": "get('current_record.field_424')",
                "navigate_to_url": "get('current_record.field_424')",
                "page_parameters": [
                    {"name": "id", "value": "get('current_record.field_424')"}
                ],
                "roles": [],
                "role_type": Element.ROLE_TYPES.ALLOW_ALL,
            },
        ],
        "data_sources": [
            {
                "id": 3,
                "name": "Data source",
                "order": "1.00000000000000000000",
                "service": {
                    "id": 4,
                    "integration_id": integration.id,
                    "type": "local_baserow_list_rows",
                    "table_id": 424,
                    "view_id": None,
                    "search_query": "",
                    "filter_type": "AND",
                    "filters": [],
                    "sortings": [],
                },
            }
        ],
        "workflow_actions": [
            {
                "id": 3,
                "type": "notification",
                "order": 1,
                "page_id": 5,
                "element_id": 29,
                "event": "click",
                "title": "get('current_record.field_424')",
                "description": "",
            }
        ],
    }

    id_mapping = defaultdict(MirrorDict)
    id_mapping["database_fields"] = {424: field.id}
    id_mapping["database_tables"] = {424: table.id}

    PageHandler().import_page(builder, exported, id_mapping)

    migrated_ref = f"get('current_record.{field.db_column}')"

    button = ButtonElement.objects.all().first()
    assert button.value == migrated_ref

    heading = HeadingElement.objects.all().first()
    assert heading.value == migrated_ref

    action = NotificationWorkflowAction.objects.first()
    assert action.title == migrated_ref

    link = LinkElement.objects.all().first()
    assert link.value == migrated_ref
    assert link.navigate_to_url == migrated_ref
    assert link.page_parameters[0]["value"] == migrated_ref

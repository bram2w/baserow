import pytest

from baserow.contrib.builder.elements.collection_field_types import (
    LinkCollectionFieldType,
)
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.pages.signals import page_deleted


@pytest.mark.django_db
def test_page_deletion_updates_link_collection_navigate_to_page_id(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    page = data_fixture.create_builder_page(builder=builder)
    destination_page = data_fixture.create_builder_page(builder=builder)
    table_element = data_fixture.create_builder_table_element(
        page=page,
        fields=[
            {
                "name": "Link",
                "type": "link",
                "config": {
                    "page_parameters": [],
                    "navigate_to_page_id": destination_page.id,
                    "navigation_type": "page",
                    "navigate_to_url": "",
                    "link_name": "Click me",
                    "target": "self",
                },
            },
        ],
    )
    field = table_element.fields.get(type=LinkCollectionFieldType.type)
    page_deleted.send(Page, builder=builder, page_id=destination_page.id, user=user)
    field.refresh_from_db()
    assert field.config == {
        "target": "self",
        "link_name": "Click me",
        "navigate_to_url": "",
        "navigation_type": "page",
        "page_parameters": [],
        "navigate_to_page_id": None,
    }

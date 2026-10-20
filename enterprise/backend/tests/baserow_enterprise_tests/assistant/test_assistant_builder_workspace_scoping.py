"""
Kuma's builder tools only reach objects in the chat's workspace. An ID from another
workspace the user belongs to gets the same error as a missing one, and nothing
changes.
"""

from django.db import transaction

import pytest

from baserow.contrib.builder.data_sources.models import DataSource
from baserow.contrib.builder.elements.models import Element
from baserow_enterprise.assistant.tools.builder import helpers
from baserow_enterprise.assistant.tools.builder.types import (
    DataSourceUpdate,
    ElementMove,
    ElementStyleUpdate,
    ElementUpdate,
)
from baserow_enterprise.assistant.tools.shared import ToolInputError


@pytest.fixture
def two_workspaces(data_fixture):
    user = data_fixture.create_user()
    here = data_fixture.create_workspace(user=user)
    other = data_fixture.create_workspace(user=user)
    builder = data_fixture.create_builder_application(workspace=other)
    page = data_fixture.create_builder_page(builder=builder)
    heading = data_fixture.create_builder_heading_element(page=page)
    button = data_fixture.create_builder_button_element(page=page)
    action = data_fixture.create_notification_workflow_action(
        page=page, element=button, event="click"
    )
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, name="Original"
    )
    return user, here, other, page, heading, action, data_source


@pytest.mark.django_db
def test_page_from_other_workspace_is_not_found(two_workspaces):
    user, here, other, page, *_ = two_workspaces

    with pytest.raises(ToolInputError, match=f"Page with ID {page.id} not found"):
        helpers.get_page(user, here, page.id)
    assert helpers.get_page(user, other, page.id) == page


@pytest.mark.django_db
def test_element_from_other_workspace_is_not_changed(two_workspaces):
    user, here, _, _, heading, *_ = two_workspaces
    before = Element.objects.get(id=heading.id).specific.styles

    with transaction.atomic():
        with pytest.raises(ToolInputError, match="not found"):
            helpers.update_element(user, here, ElementUpdate(element_id=heading.id))
        with pytest.raises(ToolInputError, match="not found"):
            helpers.update_element_style(
                user, here, ElementStyleUpdate(element_id=heading.id, reset=True)
            )
        with pytest.raises(ToolInputError, match="not found"):
            helpers.move_element(user, here, ElementMove(element_id=heading.id))

    assert Element.objects.get(id=heading.id).specific.styles == before


@pytest.mark.django_db
def test_data_source_from_other_workspace_is_not_changed(two_workspaces):
    user, here, other, *_, data_source = two_workspaces
    update = DataSourceUpdate(data_source_id=data_source.id, name="Changed")

    with pytest.raises(ToolInputError, match="not found"):
        helpers.update_data_source(user, update, here)
    assert DataSource.objects.get(id=data_source.id).name == "Original"

    helpers.update_data_source(user, update, other)
    assert DataSource.objects.get(id=data_source.id).name == "Changed"


@pytest.mark.django_db
def test_action_from_other_workspace_is_not_found(two_workspaces):
    user, here, *_, action, _ = two_workspaces

    with pytest.raises(ToolInputError, match=f"Action with ID {action.id} not found"):
        helpers.add_field_mapping_to_action(user, here, action.id, 1, "'x'")

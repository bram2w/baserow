import uuid

import pytest
from pytest_unordered import unordered

from baserow.contrib.database.action.scopes import ViewActionScopeType
from baserow.contrib.database.fields.actions import CreateFieldActionType
from baserow.contrib.database.views.actions import (
    RotateViewSlugActionType,
    UpdateViewActionType,
    UpdateViewFieldOptionsActionType,
)
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_update_view_field_options(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    field_1 = data_fixture.create_text_field(table=table)
    field_2 = data_fixture.create_text_field(table=table)
    field_3 = data_fixture.create_text_field(table=table)

    ViewHandler().update_field_options(
        user=user,
        view=grid_view,
        field_options={
            field_1.id: {
                "width": 150,
                "order": 0,
                "aggregation_raw_type": "empty_count",
                "aggregation_type": "empty_count",
            },
            field_2.id: {
                "width": 250,
                "order": 1,
                "aggregation_raw_type": "unique_count",
                "aggregation_type": "unique_count",
            },
            field_3.id: {
                "width": 125,
                "order": 2,
                "aggregation_raw_type": "empty_count",
                "aggregation_type": "empty_percentage",
            },
        },
    )

    original_options = grid_view.get_field_options()
    assert len(original_options) == 3
    (
        original_field_1_options,
        original_field_2_options,
        original_field_3_options,
    ) = original_options

    assert original_field_1_options.field_id == field_1.id
    assert original_field_1_options.width == 150
    assert original_field_1_options.order == 0
    assert original_field_1_options.hidden is False
    assert original_field_1_options.aggregation_raw_type == "empty_count"
    assert original_field_1_options.aggregation_type == "empty_count"

    assert original_field_2_options.field_id == field_2.id
    assert original_field_2_options.width == 250
    assert original_field_2_options.order == 1
    assert original_field_2_options.hidden is False
    assert original_field_2_options.aggregation_raw_type == "unique_count"
    assert original_field_2_options.aggregation_type == "unique_count"

    assert original_field_3_options.field_id == field_3.id
    assert original_field_3_options.width == 125
    assert original_field_3_options.order == 2
    assert original_field_3_options.hidden is False
    assert original_field_3_options.aggregation_raw_type == "empty_count"
    assert original_field_3_options.aggregation_type == "empty_percentage"

    action_type_registry.get_by_type(UpdateViewFieldOptionsActionType).do(
        user,
        grid_view,
        field_options={
            field_1.id: {
                "width": 100,
                "order": 1,
                "aggregation_raw_type": "unique_count",
                "aggregation_type": "unique_count",
            },
            field_2.id: {
                "width": 350,
                "order": 0,
                "aggregation_raw_type": "empty_count",
                "aggregation_type": "empty_percentage",
            },
            field_3.id: {"hidden": True},
        },
    )

    new_options = grid_view.get_field_options().order_by("field_id")
    assert len(new_options) == 3
    new_field_1_options, new_field_2_options, new_field_3_options = new_options

    assert new_field_1_options.field_id == field_1.id
    assert new_field_1_options.width == 100
    assert new_field_1_options.order == 1
    assert new_field_1_options.hidden is False
    assert new_field_1_options.aggregation_raw_type == "unique_count"
    assert new_field_1_options.aggregation_type == "unique_count"

    assert new_field_2_options.field_id == field_2.id
    assert new_field_2_options.width == 350
    assert new_field_2_options.order == 0
    assert new_field_2_options.hidden is False
    assert new_field_2_options.aggregation_raw_type == "empty_count"
    assert new_field_2_options.aggregation_type == "empty_percentage"

    assert new_field_3_options.field_id == field_3.id
    assert new_field_3_options.hidden is True

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(
        action_undone, [UpdateViewFieldOptionsActionType]
    )

    undo_options = grid_view.get_field_options()
    assert len(undo_options) == 3
    field_1_options, field_2_options, field_3_options = undo_options

    assert field_1_options.field_id == field_1.id
    assert field_1_options.width == original_field_1_options.width
    assert field_1_options.order == original_field_1_options.order
    assert field_1_options.hidden == original_field_1_options.hidden
    assert (
        field_1_options.aggregation_raw_type
        == original_field_1_options.aggregation_raw_type
    )
    assert field_1_options.aggregation_type == original_field_1_options.aggregation_type

    assert field_2_options.field_id == field_2.id
    assert field_2_options.width == original_field_2_options.width
    assert field_2_options.order == original_field_2_options.order
    assert field_2_options.hidden == original_field_2_options.hidden
    assert (
        field_2_options.aggregation_raw_type
        == original_field_2_options.aggregation_raw_type
    )
    assert field_2_options.aggregation_type == original_field_2_options.aggregation_type

    assert field_3_options.field_id == field_3.id
    assert field_3_options.width == original_field_3_options.width
    assert field_3_options.order == original_field_3_options.order
    assert field_3_options.hidden == original_field_3_options.hidden
    assert (
        field_3_options.aggregation_raw_type
        == original_field_3_options.aggregation_raw_type
    )
    assert field_3_options.aggregation_type == original_field_3_options.aggregation_type


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_update_view_field_options(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    field_1 = data_fixture.create_text_field(table=table)
    field_2 = data_fixture.create_text_field(table=table)
    field_3 = data_fixture.create_text_field(table=table)

    ViewHandler().update_field_options(
        user=user,
        view=grid_view,
        field_options={
            field_1.id: {
                "width": 150,
                "order": 0,
                "aggregation_raw_type": "empty_count",
                "aggregation_type": "empty_count",
            },
            field_2.id: {
                "width": 250,
                "order": 1,
                "aggregation_raw_type": "unique_count",
                "aggregation_type": "unique_count",
            },
            field_3.id: {
                "width": 125,
                "order": 2,
                "aggregation_raw_type": "empty_count",
                "aggregation_type": "empty_percentage",
            },
        },
    )

    original_options = grid_view.get_field_options()
    assert len(original_options) == 3
    (
        original_field_1_options,
        original_field_2_options,
        original_field_3_options,
    ) = original_options

    assert original_field_1_options.field_id == field_1.id
    assert original_field_1_options.width == 150
    assert original_field_1_options.order == 0
    assert original_field_1_options.hidden is False
    assert original_field_1_options.aggregation_raw_type == "empty_count"
    assert original_field_1_options.aggregation_type == "empty_count"

    assert original_field_2_options.field_id == field_2.id
    assert original_field_2_options.width == 250
    assert original_field_2_options.order == 1
    assert original_field_2_options.hidden is False
    assert original_field_2_options.aggregation_raw_type == "unique_count"
    assert original_field_2_options.aggregation_type == "unique_count"

    assert original_field_3_options.field_id == field_3.id
    assert original_field_3_options.width == 125
    assert original_field_3_options.order == 2
    assert original_field_3_options.hidden is False
    assert original_field_3_options.aggregation_raw_type == "empty_count"
    assert original_field_3_options.aggregation_type == "empty_percentage"

    action_type_registry.get_by_type(UpdateViewFieldOptionsActionType).do(
        user,
        grid_view,
        field_options={
            field_1.id: {
                "width": 100,
                "order": 1,
                "aggregation_raw_type": "unique_count",
                "aggregation_type": "unique_count",
            },
            field_2.id: {
                "width": 350,
                "order": 0,
                "aggregation_raw_type": "empty_count",
                "aggregation_type": "empty_percentage",
            },
            field_3.id: {"hidden": True},
        },
    )

    new_options = grid_view.get_field_options().order_by("field_id")
    assert len(new_options) == 3
    new_field_1_options, new_field_2_options, new_field_3_options = new_options

    assert new_field_1_options.field_id == field_1.id
    assert new_field_1_options.width == 100
    assert new_field_1_options.order == 1
    assert new_field_1_options.hidden is False
    assert new_field_1_options.aggregation_raw_type == "unique_count"
    assert new_field_1_options.aggregation_type == "unique_count"

    assert new_field_2_options.field_id == field_2.id
    assert new_field_2_options.width == 350
    assert new_field_2_options.order == 0
    assert new_field_2_options.hidden is False
    assert new_field_2_options.aggregation_raw_type == "empty_count"
    assert new_field_2_options.aggregation_type == "empty_percentage"

    assert new_field_3_options.field_id == field_3.id
    assert new_field_3_options.hidden is True

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(
        action_redone, [UpdateViewFieldOptionsActionType]
    )

    redo_options = grid_view.get_field_options().order_by("field_id")
    assert len(redo_options) == 3
    field_1_options, field_2_options, field_3_options = redo_options

    assert field_1_options.field_id == field_1.id
    assert field_1_options.width == new_field_1_options.width
    assert field_1_options.order == new_field_1_options.order
    assert field_1_options.hidden == new_field_1_options.hidden
    assert (
        field_1_options.aggregation_raw_type == new_field_1_options.aggregation_raw_type
    )
    assert field_1_options.aggregation_type == new_field_1_options.aggregation_type

    assert field_2_options.field_id == field_2.id
    assert field_2_options.width == new_field_2_options.width
    assert field_2_options.order == new_field_2_options.order
    assert field_2_options.hidden == new_field_2_options.hidden
    assert (
        field_2_options.aggregation_raw_type == new_field_2_options.aggregation_raw_type
    )
    assert field_2_options.aggregation_type == new_field_2_options.aggregation_type

    assert field_3_options.field_id == field_3.id
    assert field_3_options.width == new_field_3_options.width
    assert field_3_options.order == new_field_3_options.order
    assert field_3_options.hidden == new_field_3_options.hidden
    assert (
        field_3_options.aggregation_raw_type == new_field_3_options.aggregation_raw_type
    )
    assert field_3_options.aggregation_type == new_field_3_options.aggregation_type


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_rotate_view_slug(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    original_view_slug = grid_view.slug

    action_type_registry.get_by_type(RotateViewSlugActionType).do(user, grid_view)

    grid_view.refresh_from_db()
    new_view_slug = grid_view.slug
    assert new_view_slug != original_view_slug

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_undone, [RotateViewSlugActionType])

    grid_view.refresh_from_db()
    assert grid_view.slug == original_view_slug


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_rotate_view_slug(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    original_view_slug = grid_view.slug

    action_type_registry.get_by_type(RotateViewSlugActionType).do(user, grid_view)

    grid_view.refresh_from_db()
    new_view_slug = grid_view.slug
    assert new_view_slug != original_view_slug

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_redone, [RotateViewSlugActionType])

    grid_view.refresh_from_db()
    assert grid_view.slug == new_view_slug


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_update_view_name(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table, name="Original name")

    grid_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user, grid_view, name="New name"
    )

    assert grid_view.name == "New name"

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_undone, [UpdateViewActionType])

    grid_view.refresh_from_db()
    assert grid_view.name == "Original name"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_update_view_name(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table, name="Original name")

    grid_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user, grid_view, name="New name"
    )

    assert grid_view.name == "New name"

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_redone, [UpdateViewActionType])

    grid_view.refresh_from_db()
    assert grid_view.name == "New name"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_update_view_set_view_public(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    grid_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user, grid_view, public=True
    )

    assert grid_view.public is True

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_undone, [UpdateViewActionType])

    grid_view.refresh_from_db()
    assert grid_view.public is False


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_update_view_set_view_public(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    grid_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user, grid_view, public=True
    )

    assert grid_view.public is True

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_redone, [UpdateViewActionType])

    grid_view.refresh_from_db()
    assert grid_view.public is True


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_update_view_set_view_public_with_password(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    grid_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user,
        grid_view,
        public=True,
        public_view_password=View.make_password("password"),
    )

    assert grid_view.public is True
    assert grid_view.check_public_view_password("password") is True

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_undone, [UpdateViewActionType])

    grid_view.refresh_from_db()
    assert grid_view.public is False
    assert grid_view.check_public_view_password("") is True


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_update_view_set_view_public_with_password(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    grid_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user,
        grid_view,
        public=True,
        public_view_password=View.make_password("password"),
    )

    assert grid_view.public is True
    assert grid_view.check_public_view_password("password") is True

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_redone, [UpdateViewActionType])

    grid_view.refresh_from_db()
    assert grid_view.public is True
    assert grid_view.check_public_view_password("password") is True


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_update_view_filter_type(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    grid_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user,
        grid_view,
        filter_type="OR",
    )

    assert grid_view.filter_type == "OR"

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_undone, [UpdateViewActionType])

    grid_view.refresh_from_db()
    assert grid_view.filter_type == "AND"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_update_view_filter_type(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    grid_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user,
        grid_view,
        filter_type="OR",
    )

    assert grid_view.filter_type == "OR"

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_redone, [UpdateViewActionType])

    grid_view.refresh_from_db()
    assert grid_view.filter_type == "OR"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_update_view_filters_disabled(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    grid_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user,
        grid_view,
        filters_disabled=True,
    )

    assert grid_view.filters_disabled is True

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_undone, [UpdateViewActionType])

    grid_view.refresh_from_db()
    assert grid_view.filters_disabled is False


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_update_view_filters_disabled(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    grid_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user,
        grid_view,
        filters_disabled=True,
    )

    assert grid_view.filters_disabled is True

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_redone, [UpdateViewActionType])

    grid_view.refresh_from_db()
    assert grid_view.filters_disabled is True


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_update_form_view(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)
    user_file_1 = data_fixture.create_user_file()
    user_file_2 = data_fixture.create_user_file()

    original_form_data = {
        "name": "Test Form original",
        "public": True,
        "title": "Title Form original",
        "description": "Description of Form original",
        "cover_image": user_file_1,
        "logo_image": user_file_1,
        "submit_text": "Patched Submit original",
        "submit_action": "REDIRECT TO ORIGINAL URL",
        "submit_action_redirect_url": "https://localhost/original",
    }

    form_view_with_changes = ViewHandler().update_view(
        user, form_view, **original_form_data
    )
    form_view = form_view_with_changes.updated_view_instance

    assert form_view.name == original_form_data["name"]
    assert form_view.public == original_form_data["public"]
    assert form_view.title == original_form_data["title"]
    assert form_view.description == original_form_data["description"]
    assert form_view.cover_image.name == user_file_1.name
    assert form_view.logo_image.name == user_file_1.name
    assert form_view.submit_text == original_form_data["submit_text"]
    assert form_view.submit_action == original_form_data["submit_action"]
    assert (
        form_view.submit_action_redirect_url
        == original_form_data["submit_action_redirect_url"]
    )

    new_form_data = {
        "name": "Test Form new",
        "public": False,
        "title": "Title Form new",
        "submit_text": "Patched Submit new",
        "description": "Description of Form new",
        "cover_image": user_file_2,
        "logo_image": user_file_2,
        "submit_action": "REDIRECT TO NEW URL",
        "submit_action_redirect_url": "https://localhost/new",
    }

    form_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user, form_view, **new_form_data
    )

    assert form_view.name == new_form_data["name"]
    assert form_view.public == new_form_data["public"]
    assert form_view.title == new_form_data["title"]
    assert form_view.description == new_form_data["description"]
    assert form_view.cover_image.name == user_file_2.name
    assert form_view.logo_image.name == user_file_2.name
    assert form_view.submit_text == new_form_data["submit_text"]
    assert form_view.submit_action == new_form_data["submit_action"]
    assert (
        form_view.submit_action_redirect_url
        == new_form_data["submit_action_redirect_url"]
    )

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(form_view.id)], session_id
    )

    form_view.refresh_from_db()
    assert_undo_redo_actions_are_valid(action_undone, [UpdateViewActionType])

    assert form_view.name == original_form_data["name"]
    assert form_view.public == original_form_data["public"]
    assert form_view.title == original_form_data["title"]
    assert form_view.description == original_form_data["description"]
    assert form_view.cover_image.name == user_file_1.name
    assert form_view.logo_image.name == user_file_1.name
    assert form_view.submit_text == original_form_data["submit_text"]
    assert form_view.submit_action == original_form_data["submit_action"]
    assert (
        form_view.submit_action_redirect_url
        == original_form_data["submit_action_redirect_url"]
    )

    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(form_view.id)], session_id
    )

    form_view.refresh_from_db()
    assert_undo_redo_actions_are_valid(action_redone, [UpdateViewActionType])

    assert form_view.name == new_form_data["name"]
    assert form_view.public == new_form_data["public"]
    assert form_view.title == new_form_data["title"]
    assert form_view.description == new_form_data["description"]
    assert form_view.cover_image.name == user_file_2.name
    assert form_view.logo_image.name == user_file_2.name
    assert form_view.submit_text == new_form_data["submit_text"]
    assert form_view.submit_action == new_form_data["submit_action"]
    assert (
        form_view.submit_action_redirect_url
        == new_form_data["submit_action_redirect_url"]
    )


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_update_gallery_view(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    gallery_view = data_fixture.create_gallery_view(table=table)
    file_field_1 = data_fixture.create_file_field(table=table)
    file_field_2 = data_fixture.create_file_field(table=table)

    original_gallery_data = {
        "name": "Test Original Gallery",
        "filter_type": "AND",
        "filters_disabled": False,
        "card_cover_image_field": file_field_1,
    }

    gallery_view_with_changes = ViewHandler().update_view(
        user, gallery_view, **original_gallery_data
    )
    gallery_view = gallery_view_with_changes.updated_view_instance

    assert gallery_view.name == original_gallery_data["name"]
    assert gallery_view.filter_type == original_gallery_data["filter_type"]
    assert gallery_view.filters_disabled == original_gallery_data["filters_disabled"]
    assert gallery_view.card_cover_image_field.id == file_field_1.id

    new_gallery_data = {
        "name": "Test New Gallery",
        "filter_type": "OR",
        "filters_disabled": True,
        "card_cover_image_field": file_field_2,
    }

    gallery_view = action_type_registry.get_by_type(UpdateViewActionType).do(
        user, gallery_view, **new_gallery_data
    )

    assert gallery_view.name == new_gallery_data["name"]
    assert gallery_view.filter_type == new_gallery_data["filter_type"]
    assert gallery_view.filters_disabled == new_gallery_data["filters_disabled"]
    assert gallery_view.card_cover_image_field.id == file_field_2.id

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(gallery_view.id)], session_id
    )

    gallery_view.refresh_from_db()
    assert_undo_redo_actions_are_valid(action_undone, [UpdateViewActionType])

    assert gallery_view.name == original_gallery_data["name"]
    assert gallery_view.filter_type == original_gallery_data["filter_type"]
    assert gallery_view.filters_disabled == original_gallery_data["filters_disabled"]
    assert gallery_view.card_cover_image_field.id == file_field_1.id

    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(gallery_view.id)], session_id
    )

    gallery_view.refresh_from_db()
    assert_undo_redo_actions_are_valid(action_redone, [UpdateViewActionType])

    assert gallery_view.name == new_gallery_data["name"]
    assert gallery_view.filter_type == new_gallery_data["filter_type"]
    assert gallery_view.filters_disabled == new_gallery_data["filters_disabled"]
    assert gallery_view.card_cover_image_field.id == file_field_2.id


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_insert_field_in_action_group(data_fixture):
    session_id, action_group = "session-id", uuid.uuid4()
    user = data_fixture.create_user(session_id=session_id, action_group=action_group)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    field_1 = data_fixture.create_text_field(table=table)
    field_2 = data_fixture.create_text_field(table=table)

    ViewHandler().update_field_options(
        user=user,
        view=grid_view,
        field_options={
            field_1.id: {
                "width": 150,
                "order": 0,
                "aggregation_raw_type": "",
                "aggregation_type": "",
            },
            field_2.id: {
                "width": 150,
                "order": 1,
                "aggregation_raw_type": "",
                "aggregation_type": "",
            },
        },
    )

    # insert left/right is an action workspace composed of two actions:
    # 1. create field
    # 2. update fields options

    new_field = action_type_registry.get_by_type(CreateFieldActionType).do(
        user, table, "number", name="to the right of field_1"
    )

    action_type_registry.get_by_type(UpdateViewFieldOptionsActionType).do(
        user,
        grid_view,
        field_options={
            field_1.id: {
                "width": 150,
                "order": 0,
                "aggregation_raw_type": "",
                "aggregation_type": "",
            },
            new_field.id: {
                "width": 150,
                "order": 1,
                "aggregation_raw_type": "",
                "aggregation_type": "",
            },
            field_2.id: {
                "width": 150,
                "order": 2,
                "aggregation_raw_type": "",
                "aggregation_type": "",
            },
        },
    )

    updated_options = grid_view.get_field_options()
    assert len(updated_options) == 3

    assert [
        {
            "id": fo.field_id,
            "order": fo.order,
        }
        for fo in updated_options
    ] == unordered(
        [
            {"id": field_1.id, "order": 0},
            {"id": new_field.id, "order": 1},
            {"id": field_2.id, "order": 2},
        ]
    )

    undone_actions = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(
        undone_actions, [UpdateViewFieldOptionsActionType, CreateFieldActionType]
    )

    original_options = grid_view.get_field_options()
    assert len(original_options) == 2
    assert [
        {
            "id": fo.field_id,
            "order": fo.order,
        }
        for fo in original_options
    ] == unordered(
        [
            {"id": field_1.id, "order": 0},
            {"id": field_2.id, "order": 1},
        ]
    )

    redone_actions = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(
        redone_actions, [CreateFieldActionType, UpdateViewFieldOptionsActionType]
    )

    updated_options = grid_view.get_field_options()
    assert len(updated_options) == 3

    assert [
        {
            "id": fo.field_id,
            "order": fo.order,
        }
        for fo in updated_options
    ] == unordered(
        [
            {"id": field_1.id, "order": 0},
            {"id": new_field.id, "order": 1},
            {"id": field_2.id, "order": 2},
        ]
    )

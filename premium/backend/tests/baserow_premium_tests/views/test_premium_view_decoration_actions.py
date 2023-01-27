from django.test.utils import override_settings

import pytest

from baserow.contrib.database.action.scopes import ViewActionScopeType
from baserow.contrib.database.views.actions import (
    CreateDecorationActionType,
    DeleteDecorationActionType,
    UpdateDecorationActionType,
)
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import ViewDecoration
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_create_decoration(premium_data_fixture):
    session_id = "session-id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    view = premium_data_fixture.create_grid_view(user=user)
    decorator_type_name = "left_border_color"
    value_provider_type_name = ""
    value_provider_conf = {}

    action_type_registry.get_by_type(CreateDecorationActionType).do(
        view,
        decorator_type_name,
        value_provider_type_name,
        value_provider_conf,
        user=user,
    )

    assert ViewDecoration.objects.count() == 1

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_undone, [CreateDecorationActionType])

    assert ViewDecoration.objects.count() == 0


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_redo_create_decoration(premium_data_fixture):
    session_id = "session-id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    view = premium_data_fixture.create_grid_view(user=user)
    decorator_type_name = "left_border_color"
    value_provider_type_name = ""
    value_provider_conf = {}

    action_type_registry.get_by_type(CreateDecorationActionType).do(
        view,
        decorator_type_name,
        value_provider_type_name,
        value_provider_conf,
        user=user,
    )

    ActionHandler.undo(user, [ViewActionScopeType.value(view.id)], session_id)
    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_redone, [CreateDecorationActionType])

    assert ViewDecoration.objects.count() == 1


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_update_decoration(premium_data_fixture):
    session_id = "session-id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    view = premium_data_fixture.create_grid_view(user=user)
    decorator_type_name = "left_border_color"
    value_provider_type_name = ""
    value_provider_conf = {}

    view_decoration = ViewHandler().create_decoration(
        view,
        decorator_type_name,
        value_provider_type_name,
        value_provider_conf,
        user=user,
    )

    action_type_registry.get_by_type(UpdateDecorationActionType).do(
        view_decoration, decorator_type_name="background_color", user=user
    )

    view_decoration.refresh_from_db()
    assert view_decoration.type == "background_color"

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_undone, [UpdateDecorationActionType])

    view_decoration.refresh_from_db()
    assert view_decoration.type == decorator_type_name


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_redo_update_decoration(premium_data_fixture):
    session_id = "session-id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    view = premium_data_fixture.create_grid_view(user=user)
    decorator_type_name = "left_border_color"
    value_provider_type_name = ""
    value_provider_conf = {}

    view_decoration = ViewHandler().create_decoration(
        view,
        decorator_type_name,
        value_provider_type_name,
        value_provider_conf,
        user=user,
    )

    action_type_registry.get_by_type(UpdateDecorationActionType).do(
        view_decoration, decorator_type_name="background_color", user=user
    )

    ActionHandler.undo(user, [ViewActionScopeType.value(view.id)], session_id)
    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_redone, [UpdateDecorationActionType])

    view_decoration.refresh_from_db()
    assert view_decoration.type == "background_color"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_delete_decoration(premium_data_fixture):
    session_id = "session-id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    view = premium_data_fixture.create_grid_view(user=user)
    decorator_type_name = "left_border_color"
    value_provider_type_name = ""
    value_provider_conf = {}
    order = 3

    view_decoration = ViewHandler().create_decoration(
        view,
        decorator_type_name,
        value_provider_type_name,
        value_provider_conf,
        user=user,
        order=order,
    )

    view_decoration_id = view_decoration.id

    action_type_registry.get_by_type(DeleteDecorationActionType).do(
        view_decoration, user=user
    )

    action_undone = ActionHandler.undo(
        user, [ViewActionScopeType.value(view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_undone, [DeleteDecorationActionType])

    assert ViewDecoration.objects.count() == 1

    view_decoration = ViewHandler().get_decoration(user, view_decoration_id)
    assert view_decoration.order == order


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_redo_delete_decoration(premium_data_fixture):
    session_id = "session-id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    view = premium_data_fixture.create_grid_view(user=user)
    decorator_type_name = "left_border_color"
    value_provider_type_name = ""
    value_provider_conf = {}

    view_decoration = ViewHandler().create_decoration(
        view,
        decorator_type_name,
        value_provider_type_name,
        value_provider_conf,
        user=user,
    )

    action_type_registry.get_by_type(DeleteDecorationActionType).do(
        view_decoration, user=user
    )

    ActionHandler.undo(user, [ViewActionScopeType.value(view.id)], session_id)
    action_redone = ActionHandler.redo(
        user, [ViewActionScopeType.value(view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(action_redone, [DeleteDecorationActionType])

    assert ViewDecoration.objects.count() == 0

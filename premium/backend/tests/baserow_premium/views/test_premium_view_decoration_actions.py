import pytest

from django.test.utils import override_settings

from baserow.contrib.database.views.actions import (
    CreateDecorationActionType,
    UpdateDecorationActionType,
    DeleteDecorationActionType,
)
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import ViewDecoration
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.action.scopes import ViewActionScopeType


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

    assert action_undone is not None
    assert action_undone.type == CreateDecorationActionType.type
    assert action_undone.error is None

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

    assert action_redone is not None
    assert action_redone.type == CreateDecorationActionType.type
    assert action_redone.error is None

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

    assert action_undone is not None
    assert action_undone.type == UpdateDecorationActionType.type
    assert action_undone.error is None

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

    assert action_redone is not None
    assert action_redone.type == UpdateDecorationActionType.type
    assert action_redone.error is None

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

    assert action_undone is not None
    assert action_undone.type == DeleteDecorationActionType.type
    assert action_undone.error is None

    assert ViewDecoration.objects.count() == 1

    view_decoration = ViewHandler().get_decoration(view_decoration_id)
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

    assert action_redone is not None
    assert action_redone.type == DeleteDecorationActionType.type
    assert action_redone.error is None

    assert ViewDecoration.objects.count() == 0

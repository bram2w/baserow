import os

from django.conf import settings
from django.test import override_settings

import pytest

from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.action.scopes import WorkspaceActionScopeType
from baserow.core.actions import InstallTemplateActionType
from baserow.core.handler import CoreHandler
from baserow.core.models import Application, Template
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid

TEST_TEMPLATES_DIR = os.path.join(settings.BASE_DIR, "../../../tests/templates")


@pytest.mark.django_db
@pytest.mark.undo_redo
@override_settings(APPLICATION_TEMPLATES_DIR=TEST_TEMPLATES_DIR)
def test_can_undo_redo_install_template(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)
    handler = CoreHandler()
    handler.sync_templates()

    template = Template.objects.get(slug="example-template")

    installed_applications = action_type_registry.get_by_type(
        InstallTemplateActionType
    ).do(user, workspace, template)

    assert len(installed_applications) == 1
    assert Application.objects.get(pk=installed_applications[0].id) is not None

    undone_actions = ActionHandler.undo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )
    assert_undo_redo_actions_are_valid(undone_actions, [InstallTemplateActionType])
    with pytest.raises(Application.DoesNotExist):
        Application.objects.get(pk=installed_applications[0].id)

    actions_redone = ActionHandler.redo(
        user, [WorkspaceActionScopeType.value(workspace_id=workspace.id)], session_id
    )
    assert_undo_redo_actions_are_valid(actions_redone, [InstallTemplateActionType])

    assert Application.objects.get(pk=installed_applications[0].id) is not None

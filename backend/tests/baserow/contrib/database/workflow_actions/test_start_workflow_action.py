from unittest.mock import patch

from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK

from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType
from baserow.contrib.automation.workflows.operations import (
    ReadAutomationWorkflowOperationType,
)
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.workflow_actions.models import (
    CoreStartWorkflowWorkflowAction,
    DatabaseWorkflowAction,
)
from baserow.contrib.database.workflow_actions.registries import (
    database_workflow_action_type_registry,
)
from baserow.contrib.integrations.core.models import CoreStartWorkflowService
from baserow.core.deferred_callbacks import deferred_callback_context
from baserow.core.exceptions import PermissionException
from baserow.core.handler import CoreHandler
from baserow.core.registries import ImportExportConfig


def _denying(operation_name: str):
    """A `check_permissions` that refuses one operation and defers the rest."""

    real = CoreHandler.check_permissions

    def check_permissions(self, actor, name, *args, **kwargs):
        if name == operation_name:
            raise PermissionException(f"cannot {name}")
        return real(self, actor, name, *args, **kwargs)

    return check_permissions


def _duplicate_config(user=None) -> ImportExportConfig:
    """What every copy that stays inside the instance is imported with."""

    return ImportExportConfig(
        include_permission_data=True,
        reduce_disk_space_usage=False,
        is_duplicate=True,
        exclude_sensitive_data=False,
        copied_by=user,
    )


def _button(data_fixture, user, workspace):
    database = data_fixture.create_database_application(user=user, workspace=workspace)
    table = data_fixture.create_database_table(user=user, database=database)
    return data_fixture.create_button_field(table=table)


def _workflow(data_fixture, user, workspace, **kwargs):
    automation = data_fixture.create_automation_application(
        user=user, workspace=workspace
    )
    kwargs.setdefault("trigger_type", CoreManualTriggerNodeType.type)
    return data_fixture.create_automation_workflow(
        user=user, automation=automation, **kwargs
    )


def _action_starting(data_fixture, field, workflow):
    """A start workflow action on `field`, already pointed at `workflow`."""

    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=field
    )
    CoreStartWorkflowService.objects.filter(id=action.service_id).update(
        workflow=workflow
    )
    # The fixture handed the action its exact service instance, which the FK
    # descriptor now caches. A row updated by id, not through it, needs this
    # to reach an export.
    action.service.refresh_from_db()
    return action


@pytest.mark.django_db
def test_create_a_start_workflow_action(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    button_field = data_fixture.create_button_field(table=table)

    response = api_client.post(
        reverse(
            "api:database:workflow_actions:list",
            kwargs={"field_id": button_field.id},
        ),
        {"type": "start_workflow"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK, response.json()
    data = response.json()
    assert data["type"] == "start_workflow"
    # The action names its own service type, so the editor never sends it.
    assert data["service"]["type"] == "start_workflow"
    assert CoreStartWorkflowWorkflowAction.objects.count() == 1


@pytest.mark.django_db
def test_a_workflow_the_user_can_read_is_kept(api_client, data_fixture):
    from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType

    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(user=user, workspace=workspace)
    table = data_fixture.create_database_table(user=user, database=database)
    button_field = data_fixture.create_button_field(table=table)
    automation = data_fixture.create_automation_application(
        user=user, workspace=workspace
    )
    workflow = data_fixture.create_automation_workflow(
        user=user,
        automation=automation,
        trigger_type=CoreManualTriggerNodeType.type,
    )
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=button_field
    )

    response = api_client.patch(
        reverse(
            "api:database:workflow_actions:item",
            kwargs={"workflow_action_id": action.id},
        ),
        {"service": {"workflow_id": workflow.id}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK, response.json()
    action.refresh_from_db()
    assert action.service.specific.workflow_id == workflow.id


@pytest.mark.django_db
def test_a_workflow_from_another_workspace_is_refused(api_client, data_fixture):
    """
    The shared service type only checks that the person configuring the
    button may read the workflow, and a user is often in more than one
    workspace. Without this, workspace B's workflow ends up behind workspace
    A's button, where every editor of A can fire it.
    """

    from rest_framework.status import HTTP_400_BAD_REQUEST

    from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType

    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    button_field = data_fixture.create_button_field(table=table)
    elsewhere = data_fixture.create_workspace(user=user)
    automation = data_fixture.create_automation_application(
        user=user, workspace=elsewhere
    )
    workflow = data_fixture.create_automation_workflow(
        user=user,
        automation=automation,
        trigger_type=CoreManualTriggerNodeType.type,
    )
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=button_field
    )

    response = api_client.patch(
        reverse(
            "api:database:workflow_actions:item",
            kwargs={"workflow_action_id": action.id},
        ),
        {"service": {"workflow_id": workflow.id}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    action.refresh_from_db()
    assert action.service.specific.workflow_id is None


@pytest.mark.django_db
def test_a_workflow_id_that_is_not_a_workflow_is_refused(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    button_field = data_fixture.create_button_field(table=table)
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=button_field
    )

    from rest_framework.status import HTTP_400_BAD_REQUEST

    response = api_client.patch(
        reverse(
            "api:database:workflow_actions:item",
            kwargs={"workflow_action_id": action.id},
        ),
        {"service": {"workflow_id": 0}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_clearing_the_workflow_needs_no_workspace(api_client, data_fixture):
    """An explicit null takes nothing away from anyone, as with a bot in 4c."""

    from rest_framework.status import HTTP_200_OK as OK

    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    button_field = data_fixture.create_button_field(table=table)
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=button_field
    )

    response = api_client.patch(
        reverse(
            "api:database:workflow_actions:item",
            kwargs={"workflow_action_id": action.id},
        ),
        {"service": {"workflow_id": None}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == OK, response.json()


@pytest.mark.django_db
def test_an_imported_action_drops_a_workflow_from_elsewhere(data_fixture):
    from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType
    from baserow.contrib.database.workflow_actions.registries import (
        database_workflow_action_type_registry,
    )
    from baserow.contrib.integrations.core.models import CoreStartWorkflowService

    user = data_fixture.create_user()
    source_workspace = data_fixture.create_workspace(user=user)
    automation = data_fixture.create_automation_application(
        user=user, workspace=source_workspace
    )
    workflow = data_fixture.create_automation_workflow(
        user=user,
        automation=automation,
        trigger_type=CoreManualTriggerNodeType.type,
    )
    source_table = data_fixture.create_database_table(user=user)
    source_field = data_fixture.create_button_field(table=source_table)
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=source_field
    )
    CoreStartWorkflowService.objects.filter(id=action.service_id).update(
        workflow=workflow
    )
    # The fixture handed the action its exact service instance, which the FK
    # descriptor now caches. A row updated by id, not through it, needs this
    # to reach the export below.
    action.service.refresh_from_db()

    action_type = database_workflow_action_type_registry.get("start_workflow")
    exported = action_type.export_serialized(action.specific)

    elsewhere = data_fixture.create_workspace(user=user)
    target_database = data_fixture.create_database_application(
        user=user, workspace=elsewhere
    )
    target_table = data_fixture.create_database_table(
        user=user, database=target_database
    )
    target_field = data_fixture.create_button_field(table=target_table)

    with deferred_callback_context():
        imported = action_type.import_serialized(target_field, exported, {})

    assert imported.service.specific.workflow_id is None


@pytest.mark.django_db
def test_a_duplicated_action_keeps_the_workflow(data_fixture):
    from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType
    from baserow.contrib.database.workflow_actions.registries import (
        database_workflow_action_type_registry,
    )
    from baserow.contrib.integrations.core.models import CoreStartWorkflowService

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    automation = data_fixture.create_automation_application(
        user=user, workspace=workspace
    )
    workflow = data_fixture.create_automation_workflow(
        user=user,
        automation=automation,
        trigger_type=CoreManualTriggerNodeType.type,
    )
    database = data_fixture.create_database_application(user=user, workspace=workspace)
    table = data_fixture.create_database_table(user=user, database=database)
    field = data_fixture.create_button_field(table=table)
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=field
    )
    CoreStartWorkflowService.objects.filter(id=action.service_id).update(
        workflow=workflow
    )
    # The fixture handed the action its exact service instance, which the FK
    # descriptor now caches. A row updated by id, not through it, needs this
    # to reach the export below.
    action.service.refresh_from_db()

    action_type = database_workflow_action_type_registry.get("start_workflow")
    exported = action_type.export_serialized(action.specific)

    copy_field = data_fixture.create_button_field(table=table)
    with deferred_callback_context():
        imported = action_type.import_serialized(
            copy_field,
            exported,
            {},
            import_export_config=_duplicate_config(user),
        )

    assert imported.service.specific.workflow_id == workflow.id


@pytest.mark.django_db
def test_a_click_starts_the_published_workflow(data_fixture):
    from unittest.mock import patch

    from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType
    from baserow.contrib.automation.workflows.handler import AutomationWorkflowHandler
    from baserow.contrib.database.workflow_actions.service import (
        DatabaseWorkflowActionService,
    )
    from baserow.contrib.integrations.core.models import CoreStartWorkflowService

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(user=user, workspace=workspace)
    table = data_fixture.create_database_table(user=user, database=database)
    field = data_fixture.create_button_field(table=table)
    row = table.get_model().objects.create()
    automation = data_fixture.create_automation_application(
        user=user, workspace=workspace
    )
    workflow = data_fixture.create_automation_workflow(
        user=user,
        automation=automation,
        trigger_type=CoreManualTriggerNodeType.type,
    )
    published = AutomationWorkflowHandler().publish(workflow)
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=field
    )
    CoreStartWorkflowService.objects.filter(id=action.service_id).update(
        workflow=workflow
    )

    with patch(
        "baserow.contrib.automation.workflows.handler."
        "AutomationWorkflowHandler.async_start_workflow"
    ) as async_start_workflow:
        DatabaseWorkflowActionService().dispatch_workflow_actions(user, field, row)

    async_start_workflow.assert_called_once_with(published)


@pytest.mark.django_db
def test_a_click_on_an_unpublished_workflow_tells_the_clicker(data_fixture):
    from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType
    from baserow.contrib.database.workflow_actions.exceptions import (
        WorkflowActionDispatchError,
    )
    from baserow.contrib.database.workflow_actions.service import (
        DatabaseWorkflowActionService,
    )
    from baserow.contrib.integrations.core.models import CoreStartWorkflowService

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(user=user, workspace=workspace)
    table = data_fixture.create_database_table(user=user, database=database)
    field = data_fixture.create_button_field(table=table)
    row = table.get_model().objects.create()
    automation = data_fixture.create_automation_application(
        user=user, workspace=workspace
    )
    workflow = data_fixture.create_automation_workflow(
        user=user,
        automation=automation,
        trigger_type=CoreManualTriggerNodeType.type,
    )
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=field
    )
    CoreStartWorkflowService.objects.filter(id=action.service_id).update(
        workflow=workflow
    )

    with pytest.raises(WorkflowActionDispatchError) as exc:
        DatabaseWorkflowActionService().dispatch_workflow_actions(user, field, row)

    # The reason reaches the clicker rather than becoming a 500.
    assert "published" in exc.value.message


@pytest.mark.django_db
def test_a_click_on_an_unconfigured_action_tells_the_clicker(data_fixture):
    from baserow.contrib.database.workflow_actions.exceptions import (
        WorkflowActionDispatchError,
    )
    from baserow.contrib.database.workflow_actions.service import (
        DatabaseWorkflowActionService,
    )

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_button_field(table=table)
    row = table.get_model().objects.create()
    data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=field
    )

    with pytest.raises(WorkflowActionDispatchError) as exc:
        DatabaseWorkflowActionService().dispatch_workflow_actions(user, field, row)

    assert "not configured" in exc.value.message


@pytest.mark.django_db
def test_a_snapshot_and_its_restore_keep_the_workflow(data_fixture):
    """
    A snapshot is imported with `workspace=None` on purpose, to hide it from
    the system. The workspace check has to read the workspace the import is
    for instead, or the snapshot's copy loses the workflow and the restore
    hands back a button that starts nothing.
    """

    from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType
    from baserow.contrib.database.workflow_actions.models import DatabaseWorkflowAction
    from baserow.contrib.integrations.core.models import CoreStartWorkflowService
    from baserow.core.snapshots.handler import SnapshotHandler
    from baserow.core.utils import Progress

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace, order=1)
    table = data_fixture.create_database_table(database=database, name="T")
    button_field = data_fixture.create_button_field(table=table, name="btn")
    automation = data_fixture.create_automation_application(
        user=user, workspace=workspace
    )
    workflow = data_fixture.create_automation_workflow(
        user=user,
        automation=automation,
        trigger_type=CoreManualTriggerNodeType.type,
    )
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=button_field
    )
    CoreStartWorkflowService.objects.filter(id=action.service_id).update(
        workflow=workflow
    )
    action.service.refresh_from_db()

    snapshot = data_fixture.create_snapshot(
        snapshot_from_application=database, name="snap", created_by=user
    )
    SnapshotHandler().perform_create(snapshot, Progress(total=100))
    snapshot.refresh_from_db()
    restored = SnapshotHandler().perform_restore(snapshot, Progress(total=100))

    restored_button = restored.table_set.get(name="T").field_set.get(name="btn")
    (restored_action,) = DatabaseWorkflowAction.objects.filter(field=restored_button)

    assert restored_action.specific.service.specific.workflow_id == workflow.id


@pytest.mark.django_db
def test_creating_with_a_workflow_from_another_workspace_is_refused(
    api_client, data_fixture
):
    """
    The create path reads the field from the values the service injects, not
    from an existing action, so it reaches the guard by its own route.
    """

    from rest_framework.status import HTTP_400_BAD_REQUEST

    from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType

    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    button_field = data_fixture.create_button_field(table=table)
    elsewhere = data_fixture.create_workspace(user=user)
    automation = data_fixture.create_automation_application(
        user=user, workspace=elsewhere
    )
    workflow = data_fixture.create_automation_workflow(
        user=user,
        automation=automation,
        trigger_type=CoreManualTriggerNodeType.type,
    )

    response = api_client.post(
        reverse(
            "api:database:workflow_actions:list",
            kwargs={"field_id": button_field.id},
        ),
        {"type": "start_workflow", "service": {"workflow_id": workflow.id}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert CoreStartWorkflowWorkflowAction.objects.count() == 0


@pytest.mark.django_db
def test_swapping_type_to_a_workflow_from_another_workspace_is_refused(
    api_client, data_fixture
):
    """
    Changing an action's type prepares the values with no instance at all, so
    the field arrives from a third place again.
    """

    from rest_framework.status import HTTP_400_BAD_REQUEST

    from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType
    from baserow.contrib.database.workflow_actions.models import (
        OpenUrlWorkflowAction,
    )

    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    button_field = data_fixture.create_button_field(table=table)
    elsewhere = data_fixture.create_workspace(user=user)
    automation = data_fixture.create_automation_application(
        user=user, workspace=elsewhere
    )
    workflow = data_fixture.create_automation_workflow(
        user=user,
        automation=automation,
        trigger_type=CoreManualTriggerNodeType.type,
    )
    action = data_fixture.create_database_workflow_action(
        OpenUrlWorkflowAction, field=button_field
    )

    response = api_client.patch(
        reverse(
            "api:database:workflow_actions:item",
            kwargs={"workflow_action_id": action.id},
        ),
        {"type": "start_workflow", "service": {"workflow_id": workflow.id}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    action.refresh_from_db()
    assert action.specific.get_type().type == "open_url"


@pytest.mark.django_db
def test_a_file_import_drops_a_workflow_whose_id_collides(data_fixture):
    """
    Ids are one global sequence, so a file written on another installation can
    name a workflow number the destination workspace happens to own. Living in
    the workspace is not the same as being the workflow somebody chose: kept,
    the button would start work nobody picked.
    """

    user = data_fixture.create_user()
    source_workspace = data_fixture.create_workspace(user=user)
    source_field = _button(data_fixture, user, source_workspace)
    source_workflow = _workflow(data_fixture, user, source_workspace)
    action = _action_starting(data_fixture, source_field, source_workflow)

    action_type = database_workflow_action_type_registry.get("start_workflow")
    exported = action_type.export_serialized(action.specific)

    destination_workspace = data_fixture.create_workspace(user=user)
    destination_field = _button(data_fixture, user, destination_workspace)
    unrelated = _workflow(data_fixture, user, destination_workspace)
    # What the collision looks like in the file: a number this workspace owns,
    # written by an installation that meant something else by it.
    exported["service"]["workflow_id"] = unrelated.id

    with deferred_callback_context():
        imported = action_type.import_serialized(destination_field, exported, {})

    assert imported.service.specific.workflow_id is None


@pytest.mark.django_db
def test_an_import_keeps_a_workflow_it_remapped_itself(data_fixture):
    """
    The automation came along in the same import, so the id the file named has
    a copy here and the reference is this installation's.
    """

    user = data_fixture.create_user()
    source_workspace = data_fixture.create_workspace(user=user)
    source_field = _button(data_fixture, user, source_workspace)
    source_workflow = _workflow(data_fixture, user, source_workspace)
    action = _action_starting(data_fixture, source_field, source_workflow)

    action_type = database_workflow_action_type_registry.get("start_workflow")
    exported = action_type.export_serialized(action.specific)

    destination_workspace = data_fixture.create_workspace(user=user)
    destination_field = _button(data_fixture, user, destination_workspace)
    imported_workflow = _workflow(data_fixture, user, destination_workspace)
    id_mapping = {
        "automation_workflows": {source_workflow.id: imported_workflow.id},
    }

    with deferred_callback_context():
        imported = action_type.import_serialized(
            destination_field, exported, id_mapping
        )

    assert imported.service.specific.workflow_id == imported_workflow.id


@pytest.mark.django_db
def test_an_imported_action_drops_a_workflow_that_cannot_be_dispatched(data_fixture):
    """
    A save with this id would be refused, so a copy may not hold it either, or
    every click on the copy fails at dispatch with nothing said in the editor.
    """

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    field = _button(data_fixture, user, workspace)
    workflow = _workflow(data_fixture, user, workspace, create_trigger=False)
    action = _action_starting(data_fixture, field, workflow)

    action_type = database_workflow_action_type_registry.get("start_workflow")
    exported = action_type.export_serialized(action.specific)

    copy_field = data_fixture.create_button_field(table=field.table)
    with deferred_callback_context():
        imported = action_type.import_serialized(
            copy_field,
            exported,
            {},
            import_export_config=_duplicate_config(user),
        )

    assert imported.service.specific.workflow_id is None


@pytest.mark.django_db
def test_duplicating_a_table_keeps_a_workflow_the_duplicator_can_read(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    button_field = _button(data_fixture, user, workspace)
    workflow = _workflow(data_fixture, user, workspace)
    _action_starting(data_fixture, button_field, workflow)

    duplicated = TableHandler().duplicate_table(user, button_field.table)

    (copied,) = DatabaseWorkflowAction.objects.filter(field__table=duplicated)
    assert copied.specific.service.specific.workflow_id == workflow.id


@pytest.mark.django_db
def test_duplicating_a_table_drops_a_workflow_the_duplicator_cannot_read(data_fixture):
    """
    A role can reach the database without reaching the automation. The copy
    must not hand its owner a button that starts what they may not read.
    """

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    button_field = _button(data_fixture, user, workspace)
    workflow = _workflow(data_fixture, user, workspace)
    _action_starting(data_fixture, button_field, workflow)

    with patch.object(
        CoreHandler,
        "check_permissions",
        _denying(ReadAutomationWorkflowOperationType.type),
    ):
        duplicated = TableHandler().duplicate_table(user, button_field.table)

    (copied,) = DatabaseWorkflowAction.objects.filter(field__table=duplicated)
    assert copied.specific.service.specific.workflow_id is None

"""
Workflow tools shared by the clients that act for a user.
"""

from typing import Annotated, Any

from pydantic import Field

from baserow.contrib.automation.models import Automation
from baserow.contrib.automation.workflows.handler import AutomationWorkflowHandler
from baserow.contrib.automation.workflows.models import AutomationWorkflow
from baserow.contrib.automation.workflows.operations import (
    ReadAutomationWorkflowOperationType,
)
from baserow.core.handler import CoreHandler
from baserow.core.service import CoreService
from baserow.core.tools import ToolContext
from baserow.core.tools.applications import visible_applications


def get_automation_in_workspace(ctx: ToolContext, automation_id: int) -> Automation:
    """
    Get an automation of the context's workspace.

    :raises ApplicationDoesNotExist: When the automation is missing, trashed or in
        another workspace.
    """

    return CoreService().get_application(
        ctx.user,
        automation_id,
        base_queryset=Automation.objects.filter(workspace=ctx.workspace),
    )


def get_workflow_in_workspace(ctx: ToolContext, workflow_id: int) -> AutomationWorkflow:
    """
    Get a workflow of an automation in the context's workspace.

    :raises AutomationWorkflowDoesNotExist: When the workflow is missing, trashed
        or in another workspace.
    :raises PermissionException: When the user may not read it.
    """

    workflow = AutomationWorkflowHandler().get_workflow(
        workflow_id,
        base_queryset=AutomationWorkflow.objects.filter(
            automation__workspace=ctx.workspace
        ),
    )
    CoreHandler().check_permissions(
        ctx.user,
        ReadAutomationWorkflowOperationType.type,
        workspace=ctx.workspace,
        context=workflow,
    )
    return workflow


def describe_workflow(workflow: AutomationWorkflow) -> dict[str, Any]:
    return {"id": workflow.id, "name": workflow.name, "state": workflow.state}


def list_workflows(
    ctx: ToolContext,
    automation_id: Annotated[
        int | None,
        Field(
            description="The ID of the automation to list workflows for. null lists "
            "every automation in the workspace."
        ),
    ] = None,
) -> dict[str, Any]:
    """
    List the automations of the workspace with their workflows: id, name and state
    (draft, live, paused or disabled). Pass automation_id to list one automation.
    Use list_nodes to see the nodes of a workflow.
    """

    if automation_id is None:
        automations = list(visible_applications(ctx, ["automation"]))
    else:
        automations = [get_automation_in_workspace(ctx, automation_id)]

    workflows = CoreHandler().filter_queryset(
        ctx.user,
        ReadAutomationWorkflowOperationType.type,
        AutomationWorkflow.objects.filter(automation__in=automations),
        workspace=ctx.workspace,
    )
    by_automation: dict[int, list[dict[str, Any]]] = {}
    for workflow in workflows.order_by("order", "id"):
        by_automation.setdefault(workflow.automation_id, []).append(
            describe_workflow(workflow)
        )

    return {
        "automations": [
            {
                "id": automation.id,
                "name": automation.name,
                "workflows": by_automation.get(automation.id, []),
            }
            for automation in automations
        ]
    }

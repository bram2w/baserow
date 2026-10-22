from pydantic import Field

from baserow.contrib.automation.tools.types import WorkflowCreate

__all__ = ["WorkflowCreate", "WorkflowItem"]


class WorkflowItem(WorkflowCreate):
    """Existing workflow with ID."""

    id: int
    state: str = Field(
        ..., description="Workflow state: draft, live, paused, or disabled"
    )

from baserow.core.workflow_actions.types import WorkflowActionDict


class BuilderWorkflowActionDict(WorkflowActionDict):
    page_id: int
    element_id: int
    event: str

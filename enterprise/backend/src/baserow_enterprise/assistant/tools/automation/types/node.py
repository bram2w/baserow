"""
The node definitions live in ``baserow.contrib.automation.tools.types``, shared
with MCP. The read-back models are Kuma's own.
"""

from pydantic import Field, model_serializer

from baserow.contrib.automation.tools.types import (
    CANONICAL_TO_SHORT_TYPE,
    ROW_TRIGGER_TYPES,
    SUPPORTS_FORMULA,
    ActionNodeCreate,
    AutomationFieldValue,
    NodeUpdate,
    PeriodicTriggerSettings,
    RouterEdgeCreate,
    RouterEdgeUpdate,
    RowsTriggersSettings,
    TriggerNodeCreate,
)
from baserow_enterprise.assistant.types import BaseModel

__all__ = [
    "CANONICAL_TO_SHORT_TYPE",
    "ROW_TRIGGER_TYPES",
    "SUPPORTS_FORMULA",
    "ActionNodeCreate",
    "ActionNodeItem",
    "AutomationFieldValue",
    "NodeUpdate",
    "PeriodicTriggerSettings",
    "RouterBranch",
    "RouterEdgeCreate",
    "RouterEdgeUpdate",
    "RowsTriggersSettings",
    "TriggerNodeCreate",
    "TriggerNodeItem",
]


class RouterBranch(RouterEdgeCreate):
    """Existing router branch with ID."""

    id: str


class TriggerNodeItem(TriggerNodeCreate):
    """Existing trigger node with ID."""

    id: str
    http_trigger_url: str | None = Field(
        default=None, description="The URL to trigger the HTTP request"
    )


class ActionNodeItem(BaseModel):
    """Existing action node with ID — flat structure, excludes None values."""

    id: str
    label: str
    type: str
    previous_node_ref: str | None = None
    router_edge_label: str | None = None

    # (router)
    edges: list[RouterBranch] | None = None

    # (smtp_email)
    to_emails: str | None = None
    cc_emails: str | None = None
    bcc_emails: str | None = None
    subject: str | None = None
    body: str | None = None
    body_type: str | None = None

    # (slack_write_message)
    channel: str | None = None
    text: str | None = None

    # (create_row, update_row, delete_row)
    table_id: int | None = None
    row_id: str | None = None
    values: list[AutomationFieldValue] | None = None

    # (ai_agent)
    output_type: str | None = None
    choices: list[str] | None = None
    prompt: str | None = None

    @model_serializer(mode="wrap")
    def _exclude_none(self, handler):
        return {k: v for k, v in handler(self).items() if v is not None}

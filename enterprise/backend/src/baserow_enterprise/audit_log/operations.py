from baserow.core.operations import WorkspaceCoreOperationType


class ListWorkspaceAuditLogEntriesOperationType(WorkspaceCoreOperationType):
    type = "workspace.list_audit_log_entries"

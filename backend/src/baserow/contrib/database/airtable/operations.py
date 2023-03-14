from baserow.core.operations import WorkspaceCoreOperationType


class RunAirtableImportJobOperationType(WorkspaceCoreOperationType):
    type = "workspace.run_airtable_import"

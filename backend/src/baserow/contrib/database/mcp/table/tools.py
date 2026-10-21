from baserow.contrib.database.mcp import services
from baserow.contrib.database.mcp.table.schemas import (
    DeleteTableInput,
    ListDatabasesInput,
    UpdateTableInput,
)
from baserow.contrib.database.tools import tables
from baserow.core.mcp.groups import (
    GROUP_DATABASE_DELETE,
    GROUP_DATABASE_EDIT,
    GROUP_DATABASE_READ,
)
from baserow.core.mcp.models import MCPEndpoint
from baserow.core.mcp.registries import FunctionMCPTool, MCPTool
from baserow.core.tools import ToolContext, applications


class ListApplicationsMcpTool(FunctionMCPTool):
    type = "list_applications"
    group = GROUP_DATABASE_READ
    title = "List applications"
    read_only = True
    function = applications.list_applications


# TODO: remove after 2.6. Kept because existing connections allow it by name.
class ListDatabasesMcpTool(MCPTool):
    """
    List all databases in the workspace.
    Use this to discover database IDs before listing tables.
    """

    type = "list_databases"
    group = GROUP_DATABASE_READ
    title = "List databases"
    read_only = True
    input_schema = ListDatabasesInput

    def _sync_call(self, endpoint: MCPEndpoint, args: ListDatabasesInput) -> list[dict]:
        ctx = ToolContext(user=endpoint.user, workspace=endpoint.workspace)
        databases = applications.visible_applications(ctx, ["database"])
        return [{"id": db.id, "name": db.name, "order": db.order} for db in databases]


class ListTablesMcpTool(FunctionMCPTool):
    type = "list_tables"
    group = GROUP_DATABASE_READ
    title = "List tables"
    read_only = True
    function = tables.list_tables


class CreateTablesMcpTool(FunctionMCPTool):
    type = "create_tables"
    group = GROUP_DATABASE_EDIT
    title = "Create tables"
    read_only = False
    destructive = False
    function = tables.create_tables


class UpdateTableMcpTool(MCPTool):
    """
    Rename an existing table.
    Call list_tables first to get the table ID.
    """

    type = "update_table"
    group = GROUP_DATABASE_EDIT
    title = "Update table"
    destructive = True
    enabled = False
    input_schema = UpdateTableInput

    def _sync_call(self, endpoint: MCPEndpoint, args: UpdateTableInput) -> dict:
        return services.update_table(
            endpoint.user, endpoint.workspace, args.table_id, args.name
        )


class DeleteTableMcpTool(MCPTool):
    """
    Delete (trash) a table and all its rows.
    The table can be restored from trash afterwards.
    """

    type = "delete_table"
    group = GROUP_DATABASE_DELETE
    title = "Delete table"
    destructive = True
    enabled = False
    input_schema = DeleteTableInput

    def _sync_call(self, endpoint: MCPEndpoint, args: DeleteTableInput) -> str:
        services.delete_table(endpoint.user, endpoint.workspace, args.table_id)
        return "Table successfully deleted."


class GetTableSchemaMcpTool(FunctionMCPTool):
    type = "get_table_schema"
    group = GROUP_DATABASE_READ
    title = "Get table schema"
    read_only = True
    function = tables.get_table_schema

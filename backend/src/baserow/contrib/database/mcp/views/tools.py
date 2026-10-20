from baserow.contrib.database.tools import views
from baserow.core.mcp.groups import GROUP_DATABASE_READ
from baserow.core.mcp.registries import FunctionMCPTool


class ListViewsMcpTool(FunctionMCPTool):
    type = "list_views"
    group = GROUP_DATABASE_READ
    title = "List views"
    read_only = True
    function = views.list_views

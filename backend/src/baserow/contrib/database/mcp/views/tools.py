from baserow.contrib.database.tools import views
from baserow.core.mcp.groups import GROUP_DATABASE_EDIT, GROUP_DATABASE_READ
from baserow.core.mcp.registries import FunctionMCPTool


class ListViewsMcpTool(FunctionMCPTool):
    type = "list_views"
    group = GROUP_DATABASE_READ
    title = "List views"
    read_only = True
    function = views.list_views


class CreateViewsMcpTool(FunctionMCPTool):
    type = "create_views"
    group = GROUP_DATABASE_EDIT
    title = "Create views"
    read_only = False
    destructive = False
    function = views.create_views


class CreateViewFiltersMcpTool(FunctionMCPTool):
    type = "create_view_filters"
    group = GROUP_DATABASE_EDIT
    title = "Create view filters"
    read_only = False
    destructive = False
    function = views.create_view_filters

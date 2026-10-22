from baserow.contrib.automation.tools import nodes
from baserow.core.mcp.groups import GROUP_AUTOMATION_READ
from baserow.core.mcp.registries import FunctionMCPTool


class ListNodesMcpTool(FunctionMCPTool):
    type = "list_nodes"
    group = GROUP_AUTOMATION_READ
    title = "List workflow nodes"
    read_only = True
    function = nodes.list_nodes

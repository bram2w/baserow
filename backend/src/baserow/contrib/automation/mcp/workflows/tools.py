from baserow.contrib.automation.tools import workflows
from baserow.core.mcp.groups import GROUP_AUTOMATION_READ
from baserow.core.mcp.registries import FunctionMCPTool


class ListWorkflowsMcpTool(FunctionMCPTool):
    type = "list_workflows"
    group = GROUP_AUTOMATION_READ
    title = "List workflows"
    read_only = True
    function = workflows.list_workflows

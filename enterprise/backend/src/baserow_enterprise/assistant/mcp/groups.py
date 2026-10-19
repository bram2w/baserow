from baserow.core.mcp.groups import (
    AREA_AUTOMATION,
    AREA_BUILDER,
    AREA_DOCS,
    GROUP_AUTOMATION_EDIT,
    GROUP_AUTOMATION_READ,
    GROUP_BUILDER_EDIT,
    GROUP_BUILDER_READ,
    GROUP_DOCS,
    MCPToolGroup,
)


class BuilderReadMCPToolGroup(MCPToolGroup):
    type = GROUP_BUILDER_READ
    title = "Read applications"
    area = AREA_BUILDER
    read_only_preset = True
    order = 40


class BuilderEditMCPToolGroup(MCPToolGroup):
    type = GROUP_BUILDER_EDIT
    title = "Edit applications"
    area = AREA_BUILDER
    order = 50


class AutomationReadMCPToolGroup(MCPToolGroup):
    type = GROUP_AUTOMATION_READ
    title = "Read automations"
    area = AREA_AUTOMATION
    read_only_preset = True
    order = 60


class AutomationEditMCPToolGroup(MCPToolGroup):
    type = GROUP_AUTOMATION_EDIT
    title = "Edit automations"
    area = AREA_AUTOMATION
    order = 70


class DocsMCPToolGroup(MCPToolGroup):
    type = GROUP_DOCS
    title = "Search the documentation"
    area = AREA_DOCS
    read_only_preset = True
    order = 80

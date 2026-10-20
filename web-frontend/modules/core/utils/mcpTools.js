/**
 * Names of the tools the "Read only" preset picks: the read-only tools in a
 * group with `read_only_preset`, in the listed order.
 */
export function readOnlyToolNames(tools, groups) {
  const preset = new Set(
    groups.filter((group) => group.read_only_preset).map((group) => group.type)
  )
  return tools
    .filter((tool) => preset.has(tool.group) && tool.read_only)
    .map((tool) => tool.name)
}

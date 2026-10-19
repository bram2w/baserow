/**
 * Names of the tools the "Read only" preset picks: the tools in a group with
 * `read_only_preset`, leaving out anything destructive, in the listed order.
 */
export function readOnlyToolNames(tools, groups) {
  const preset = new Set(
    groups.filter((group) => group.read_only_preset).map((group) => group.type)
  )
  return tools
    .filter((tool) => preset.has(tool.group) && !tool.destructive)
    .map((tool) => tool.name)
}

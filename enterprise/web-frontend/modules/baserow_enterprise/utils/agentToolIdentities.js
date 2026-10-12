/**
 * Helpers for tools that run as another workspace agent than the
 * application's identity: the `tool_identities` map of the workspace tool
 * config and the `identity_id` of action tools.
 */

// The identity value of a tool that acts on behalf of the Baserow user of
// the conversation instead of a workspace agent.
export const ACT_AS_USER = 'user'

// Built-in role uids by the amount of access they grant, so a per-tool
// identity can be flagged when it may do more than the agent itself.
const ROLE_RANK = {
  NO_ACCESS: 0,
  VIEWER: 1,
  COMMENTER: 2,
  EDITOR: 3,
  BUILDER: 4,
  ADMIN: 5,
}

export function roleRank(roleUid) {
  return ROLE_RANK[roleUid] ?? null
}

/**
 * Whether `identity` may do more in the workspace than `agentIdentity`.
 * Custom roles have no known rank and never raise the flag.
 */
export function hasMoreAccess(identity, agentIdentity) {
  if (!identity) {
    return false
  }
  const rank = roleRank(identity.role_uid)
  const agentRank = agentIdentity ? roleRank(agentIdentity.role_uid) : -1
  return rank !== null && agentRank !== null && rank > agentRank
}

export function workspaceToolIdentities(config) {
  const identities = config?.tool_identities
  if (!identities || typeof identities !== 'object') {
    return {}
  }
  return Object.fromEntries(
    Object.entries(identities)
      .map(([name, id]) => [name, id === ACT_AS_USER ? id : Number(id)])
      .filter(([, id]) => id === ACT_AS_USER || Number.isInteger(id))
  )
}

/**
 * Every tool that runs as someone else, for the "Exceptions" list.
 *
 * @param {object} options
 * @param {object|null} options.workspaceTool The workspace tool.
 * @param {object[]} options.actionTools The service/MCP tools.
 * @param {object[]} options.catalog The workspace tool catalog.
 * @param {object[]} options.identities The workspace agents.
 * @param {object} [options.overrides] Unsaved `tool_identities` replacing the
 *   workspace tool's own.
 * @param {object} [options.userIdentity] How a tool acting on behalf of the
 *   conversation's user is listed (`{ name }`); omitted, they aren't listed.
 */
export function listToolIdentityExceptions({
  workspaceTool,
  actionTools,
  catalog,
  identities,
  overrides = null,
  userIdentity = null,
}) {
  const byId = new Map(identities.map((identity) => [identity.id, identity]))
  if (userIdentity) {
    byId.set(ACT_AS_USER, { ...userIdentity, id: ACT_AS_USER })
  }
  const exceptions = []
  const map = overrides ?? workspaceToolIdentities(workspaceTool?.config)
  for (const [name, id] of Object.entries(map)) {
    const identity = byId.get(id)
    if (!identity) {
      continue
    }
    const catalogTool = catalog.find((tool) => tool.name === name)
    exceptions.push({
      key: `workspace-${name}`,
      kind: 'workspace',
      toolName: name,
      label: catalogTool?.label || name,
      identity,
    })
  }
  for (const tool of actionTools) {
    const identity = byId.get(tool.act_as_user ? ACT_AS_USER : tool.identity_id)
    if (!identity) {
      continue
    }
    exceptions.push({
      key: `action-${tool.id}`,
      kind: 'action',
      tool,
      toolName: tool.name,
      label: tool.name,
      identity,
    })
  }
  return exceptions
}

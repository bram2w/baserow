# ADR 010: Represent each reusable agent as a workspace application

|              |                                                |
| ------------ | ---------------------------------------------- |
| Status       | Proposed                                       |
| Date         | 2026-10-12                                     |
| Issue        | https://github.com/baserow/baserow/issues/6259 |
| Author       | Davide Silvestri (@silvestrid)                 |
| Contributors | To be confirmed                                |

## Summary

Each reusable agent will be a workspace application of type `agent`, with its own
configuration, permissions and lifecycle. Users create an Agent directly, without first
creating a builder or team and then a child agent. We prioritize a simple starting point
over the immediate complexity of grouping for future needs whose benefits are unproven.

## Context

Baserow already provides workspace application creation, navigation, roles, duplication,
export/import, templates, snapshots and trash. An agent can use these entry points as a
complete application, without introducing a subordinate agent-definition resource.

The CEO's product judgment is that users will usually start by wanting to build a single
agent. Requiring them to first name and create a builder or team introduces another
concept and management step before they can configure that agent. This is a product
judgment, rather than a conclusion established by customer research in this record.

The factors driving this decision are:

- Make creating and opening one agent a direct, familiar application operation.
- Give each agent independent access, configuration, copying and recovery boundaries.
- Reuse existing application infrastructure and supported tools and backend services.
- Avoid adding ownership, child permissions and navigation for grouped agents before
  there is a demonstrated need to manage them together.

Grouping could reduce repeated administration and provide boundaries like databases do
for tables and Application Builders do for pages. We accept the cost of reconsidering
that ownership model later if those needs become concrete. Supporting several agents
or collaboration between them does not, by itself, require a common owning application.

This record chooses the ownership and reuse boundary. The launch catalogue, execution
engine, approvals and orchestration are separate decisions. The
[delivery issue](https://github.com/baserow/baserow/issues/6259) defines release scope.

| Term               | Meaning                                                                                   |
| ------------------ | ----------------------------------------------------------------------------------------- |
| Agent application  | A workspace application representing one reusable agent and owning its configuration.     |
| Execution identity | The actor whose permissions and connections govern effects performed by an agent.         |
| Agent group        | A possible future way to manage related agents; this decision introduces no owning group. |

Baserow's existing core `Agent` is a workspace-owned permission subject. It can serve as
an execution identity and remains distinct from the configurable agent application.

## Decision

### 1. One application represents one agent

Register the application type as `agent`. Creating it creates the agent itself;
configuration belongs directly to that application. There is no builder/team parent or
child-agent creation, selection or configuration layer.

Supported callers, including conversations and automatic jobs, reference the application
ID instead of owning copies of its definition. Related agents remain independently owned
applications. Future collaboration can be evaluated using references between them;
orchestration and group management are deferred.

### 2. Use application permissions

Use the existing application scope, inherited workspace roles and individual application
assignments. Introduce no team or child-agent permission scope. Separate configuration,
invocation and conversation/run visibility: a user can use an agent without editing it
or reading another person's conversation.

Enforce permissions in backend APIs, lists and realtime events. Invocation alone does not
select the execution identity or grant direct access to tool resources. Check current
resource permissions and tool policies under the authorized execution identity when tools
run, including after resuming suspended work.

### 3. Reuse shared capabilities with explicit authorization

Adapt existing internal tools and supported backend service types, reusing input/formula
resolution, dispatch and result handling. Frontend-only actions and services requiring a
particular workflow context need separate qualification. Automations can invoke an agent
by reference without owning it.

Implementation reuse does not authorize access to another application's configured
actions or credentials. Respect connection ownership and authorization. Moving
integrations to workspaces is a planned separate change; it may reduce repeated
connection setup, but does not itself define shared agent settings or resource access.

### 4. Keep each agent's application lifecycle independent

Support duplication, export/import, templates, snapshots, trash/restore and deletion for
owned configuration. Remap references, honor permissions and sensitive-data options, and
report missing dependencies. Copies and snapshot restorations create independent agent
applications with automatic entry points disabled until explicitly enabled.

Copies exclude ordinary private conversations, live executions and pending approvals.
Trash prevents starting or resuming work; deletion preserves shared dependencies and
identities. Restoring configuration does not reverse external effects.

## Options considered

| Option                                              | Assessment                                                                                                                                                     |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| One workspace application per agent — selected      | Direct creation and independent permissions/lifecycle using existing infrastructure; managing related sets requires additional work.                           |
| Agent Builder/team application with child agents    | Provides a common boundary for roles, settings, connections and packaging, but adds an upfront concept, child permissions and navigation for an unproven need. |
| Standalone workspace-owned definitions              | Allows a separate agent catalogue, but needs new navigation and lifecycle entry points or adapters without a current requirement for that parallel model.      |
| Agents owned by Automation workflows/nodes          | Fits workflow-local tasks, but couples reusable agent ownership to one caller. Workflows remain possible callers.                                              |
| Configurable profiles inside the existing assistant | Reuses conversation UI and tools, but independently governed, portable agents would still need a managed resource model.                                       |

## Consequences

- Creating one agent requires one application and one name. There is no empty container
  to create or child list to manage. Each additional agent occupies its own application
  entry, which can make navigation more crowded as usage grows.
- Each agent has independent permissions and recovery. Workspace roles still apply,
  but managing a selected set together can require repeated application assignments,
  resource-access configuration and settings changes. The planned integration move may
  address connection reuse; shared governance and settings remain separate problems.
- **Identity and references become lasting contracts.** Agent IDs are application IDs;
  APIs, callers and exported references will build on this. Introducing an owning group
  later must preserve these contracts or migrate them and support older references.
- **Permissions and configuration ownership become costly to regroup.** Moving existing
  agents under a new parent would require explicit rules for inherited roles, resource
  access and shared settings/connections, including resolving conflicting assignments
  while preserving effective access.
- **Packaging and recovery are per agent.** Related agents have separate copy, snapshot,
  restore and deletion boundaries. Coordinated installation, versioning or recovery
  requires dependency handling and new lifecycle rules; visual grouping alone supplies
  none of those guarantees.
- Collaboration remains possible across applications. Cross-agent references need
  authorization and policies for copying, missing dependencies and deletion when that
  capability is introduced. A common owner could simplify some of that work.
- We deliberately accept possible future redesign in exchange for simpler behavior now.
  Adding a true owning group later is more expensive than choosing it before persisted
  identities, permission assignments and lifecycle contracts become established.

## Revisit triggers

- Users repeatedly assign the same roles or resource access to related agents.
- Repeated connection setup remains costly, including after workspace integrations
  become available.
- Users need shared settings across a selected group of agents, with changes propagated
  to its members.
- Customers need explicit management and access boundaries for related agents,
  analogous to databases/tables or Application Builders/pages.
- Related agents regularly need coordinated installation, release, recovery or deletion.
- Live sharing across workspaces or independently deployed runtimes requires ownership
  or identity contracts that agent applications cannot represent cleanly.

# ADR 010: Represent each reusable agent as a workspace application

|              |                                                |
| ------------ | ---------------------------------------------- |
| Status       | Proposed                                       |
| Date         | 2026-10-12                                     |
| Issue        | https://github.com/baserow/baserow/issues/6259 |
| Author       | Davide Silvestri (@silvestrid)                 |
| Contributors | Bram Wipjes                                    |

## Summary

Each reusable agent will be a workspace application of type `agent`, with its own
configuration, permissions and lifecycle. Users create and manage each agent through
Baserow's existing application entry points. We prioritize simple setup and independent
management over additional structure for potential future needs.

## Context

Baserow organizes databases and tables, Application Builders and pages, and Automations
and workflows as workspace applications containing related resources. Agents use the
same application infrastructure, with each application representing one reusable agent.
The shared infrastructure provides creation, navigation, roles, duplication,
export/import, templates, snapshots and trash entry points.

We expect users to start by building a single agent. Giving it a familiar application
entry point and independent permissions and lifecycle keeps that experience simple.
We prioritize this starting point over additional structure for shared management needs
that are not yet established.

The factors driving this decision are:

- Make creating and opening one agent a direct, familiar application operation.
- Give each agent independent access, configuration, copying and recovery boundaries.
- Reuse existing application infrastructure and supported tools and backend services.
- Keep the initial ownership and navigation model focused on individual agents;
  introduce shared management when there is a demonstrated need.

Shared management could reduce repeated administration. We accept the cost of
reconsidering the ownership model if those needs become concrete. Collaboration can be
evaluated through references between independently managed agent applications.

This record chooses the ownership and reuse boundary. The launch catalogue, execution
engine, approvals and orchestration are separate decisions. The
[delivery issue](https://github.com/baserow/baserow/issues/6259) defines release scope.

| Term               | Meaning                                                                               |
| ------------------ | ------------------------------------------------------------------------------------- |
| Agent application  | A workspace application representing one reusable agent and owning its configuration. |
| Execution identity | The actor whose permissions and connections govern effects performed by an agent.     |

Baserow's existing core `Agent` is a workspace-owned permission subject. It can serve as
an execution identity and remains distinct from the configurable agent application.

## Decision

### 1. One application represents one agent

Register the application type as `agent`. Each application represents one reusable agent
and directly owns its configuration. Creating an Agent is a standard workspace
application operation.

Supported callers, including conversations and automatic jobs, reference the application
ID instead of owning copies of its definition. Related agents remain independently owned
applications. Future collaboration can be evaluated using references between them;
orchestration and group management are deferred.

### 2. Use application permissions

Use the existing application scope, inherited workspace roles and individual application
assignments. Separate configuration, invocation and conversation/run visibility: a user
can use an agent without editing it or reading another person's conversation.

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

## Consequences

- Each agent has one name and one application entry. Creating and opening it uses
  familiar application operations. Navigation can become more crowded as the number of
  agents grows.
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

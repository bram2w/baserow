# ADR 011: Represent each reusable agent as a workspace application

|              |                                                |
| ------------ | ---------------------------------------------- |
| Status       | Proposed                                       |
| Date         | 2026-10-12                                     |
| Issue        | https://github.com/baserow/baserow/issues/6259 |
| Author       | Davide Silvestri (@silvestrid)                 |
| Contributors | Bram Wipjes                                    |

## Summary

Reusable agents need an ownership model that makes them easy to create, configure and
manage. We considered an Agent Builder application containing several agents and one
workspace application per agent. We choose one application per agent to prioritize a
simple starting experience and independent management.

## Context

Baserow organizes related resources within workspace applications: databases contain
tables, Application Builders contain pages, and Automations contain workflows. These
applications provide a common boundary for navigation, permissions and lifecycle
operations such as duplication, export/import, snapshots and trash.

Agents need a similar management boundary. Each agent has reusable configuration that
can be referenced by conversations and automatic jobs, with permissions controlling
who can configure or invoke it. The ownership model must support these needs while
keeping creation and everyday management understandable.

Both options can reuse Baserow's application infrastructure, permission system, internal
tools and supported backend services. Sharing a management boundary does not itself
authorize shared credentials, determine execution identity or provide orchestration.
The existing core `Agent` permission subject remains distinct from a configurable agent.

This record decides the ownership boundary. Execution, orchestration and the separately
planned move of integrations to workspaces are outside its scope. The
[delivery issue](https://github.com/baserow/baserow/issues/6259) defines release scope.

## Options considered

### 1. An Agent Builder application containing agents

An Agent Builder would be a workspace application containing a list of independently
configured agents, following the database-and-tables model. Users create the application
and then create agents within it. The application provides a common management boundary,
while each agent has its own identity, configuration and permission assignments.

This fits users who want to organize and administer related agents together. Roles and
shared settings can be applied at the parent, with individual agent exceptions where
needed. The application is also a natural package for copying, exporting and recovering
a related set. These benefits require a parent/child model, child management operations,
permission-filtered navigation and lifecycle handling for the agents it contains.

### 2. One workspace application per agent

Each workspace application represents one agent and directly owns its configuration.
Users create an Agent through the standard application flow, configure that agent and
open it from its application entry. Its application ID is the reference used by callers.

This gives each agent independent permissions, duplication, export/import, snapshots and
deletion through existing application operations. Related agents have separate application
entries and assignments; managing a selected set together requires additional support.

| Aspect            | Agent Builder containing agents                                                       | One application per agent                                                                             |
| ----------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Creation          | Create and name an application, then create agents within it.                         | Create and name the agent application.                                                                |
| Navigation        | One application entry with a list of agents to select.                                | One application entry per agent.                                                                      |
| Permissions       | Application roles inherited by child agents, with individual overrides.               | Workspace roles inherited by agent applications, with individual application assignments.             |
| Lifecycle         | Related agents share an application packaging and recovery boundary.                  | Each agent has an independent application packaging and recovery boundary.                            |
| Shared management | A common parent can hold roles and settings for a related set.                        | Workspace inheritance remains available; shared management of a selected set needs another mechanism. |
| Implementation    | Application infrastructure plus child CRUD, scopes, navigation and lifecycle support. | Application infrastructure applied directly to the agent.                                             |

## Decision

Represent each reusable agent as a workspace application with application type `agent`.
Each application directly owns one agent's configuration and uses application roles and
lifecycle operations. Callers reference the application ID. Configuration, invocation
and private conversation/run visibility remain separate permission concerns.

We expect users to start by wanting to build a single agent. Making that agent the
application gives them one thing to name, configure, open and manage. Independent access
and recovery boundaries also match the reusable agent as the unit that callers select.
Existing application operations support this model with less additional ownership and
permission machinery.

The Agent Builder option is consistent with Baserow's other container applications and
offers useful shared administration and packaging. However, we do not yet have established
requirements for managing agents as a related set. We prefer the clear benefits of a
simple starting point over immediate structural complexity for possible future needs.
We accept that introducing shared ownership later may require more work.

## Consequences

- Each agent has a direct creation flow and independent permissions and lifecycle. More
  agents also mean more application entries, and administering a selected set can involve
  repeated role assignments, resource-access configuration and settings changes.
- **Application identity becomes the agent identity.** APIs, callers and exported
  references will depend on application IDs. A future change to the ownership model must
  preserve those references or provide migration and compatibility handling.
- **Permissions and configuration ownership become established boundaries.** Introducing
  an owning parent later would require rules for inherited roles, shared settings and
  resource access, including how to resolve conflicts while preserving effective access.
- **Packaging and recovery are per agent.** Coordinated copying, installation, release,
  restoration or deletion of related agents will need dependency handling and additional
  lifecycle rules. Navigation grouping alone would not provide those guarantees.
- Collaboration can be designed through references between independently owned agents.
  That would still need authorization and policies for missing dependencies, copying and
  deletion; this ownership decision does not prescribe an execution model.
- The planned move to workspace integrations may reduce repeated connection setup under
  either option. Shared agent settings, resource access and governance remain separate
  needs and are not solved by changing connection ownership alone.

Introducing a common owning application would become more costly once agent IDs,
caller references, permission assignments and lifecycle contracts are in use. We accept
that potential migration cost in exchange for simplicity now, while the need for shared
ownership is uncertain.

## Revisit triggers

- Users repeatedly configure the same roles, resource access or settings across related
  agents and need those changes to propagate to a selected group.
- Repeated connection setup remains costly after workspace integrations are available.
- Customers need clear management and access boundaries for related agents, similar to
  the boundaries provided by databases/tables, Application Builders/pages or
  Automations/workflows.
- Related agents regularly need to be installed, released, recovered or deleted together.

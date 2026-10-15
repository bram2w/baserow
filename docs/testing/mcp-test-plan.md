# MCP Manual Test Plan

## Prerequisites

- A running Baserow instance (local dev or deployed)
- For OAuth: `BASEROW_MCP_OAUTH_ENABLED=true` on the backend
- An MCP-compatible client (see step 1)

## 1. Connect an MCP client

Clients connect in one of two ways. Both are under **Settings > MCP server**.

### OAuth (recommended)

The **OAuth** tab shows one URL for every client:

```
http://localhost:8000/mcp
```

CLI and desktop clients on the same machine can use `localhost`:

- **Claude Code**:
  ```bash
  claude mcp add --transport http baserow http://localhost:8000/mcp
  ```
  Run `/mcp` in Claude Code to sign in.
- **Claude Desktop**: open **Customize > Connectors**, click **+ Add**, then
  **Add custom connector** and paste the URL.
- **Codex**:
  ```bash
  codex mcp add baserow --url http://localhost:8000/mcp
  codex mcp login baserow
  ```
- **Cursor**: add this to `~/.cursor/mcp.json`:
  ```json
  { "mcpServers": { "baserow": { "url": "http://localhost:8000/mcp" } } }
  ```
- **VS Code**: add this to `.vscode/mcp.json`:
  ```json
  { "servers": { "baserow": { "type": "http", "url": "http://localhost:8000/mcp" } } }
  ```
- **Gemini CLI**:
  ```bash
  gemini mcp add -t http baserow http://localhost:8000/mcp
  ```
- **GitHub Copilot CLI**:
  ```bash
  copilot mcp add --transport http baserow http://localhost:8000/mcp
  ```
- **MCP Inspector**: run `npx @modelcontextprotocol/inspector`, choose the
  Streamable HTTP transport and paste the URL.

The [baserow-mcp README](https://github.com/baserow/baserow-mcp#install-per-agent)
covers OpenCode, Windsurf, Zed, Goose and other agents.

Hosted apps, claude.ai and ChatGPT, reach Baserow from the internet and can't
use `localhost`. Expose the backend with a tunnel, for example
`cloudflared tunnel --url http://localhost:8000`, set `PUBLIC_BACKEND_URL` to
the tunnel URL, restart the backend and use `<tunnel url>/mcp`:

- **claude.ai**: open **Customize > Connectors**, click **+ Add**, then
  **Add custom connector**, and paste the URL.
- **ChatGPT**: open **Plugins**, click **+**, choose **Add custom MCP server**,
  paste the URL and pick **OAuth** as authentication. On Business and
  Enterprise plans an admin has to allow custom MCP servers first.

The client opens the Baserow consent page. Pick a workspace and the tools to
allow, then approve. The app then shows under **Connected apps** on the OAuth
tab.

### Plugin and skill

[baserow/baserow-mcp](https://github.com/baserow/baserow-mcp) packages the
server config with the `baserow-basics` skill, which teaches the agent how to
use the tools. Test it once on a release candidate:

- **Claude Code**: the plugin asks for the server URL, so it works against a
  local stack:
  ```
  /plugin marketplace add baserow/baserow-mcp
  /plugin install baserow@baserow
  ```
  Enter `http://localhost:8000/mcp` when asked (change it later with
  `/plugin configure baserow@baserow`), then run `/mcp`, pick
  `plugin:baserow:baserow` and sign in. Remove any `baserow` server you added
  by hand first, or Claude Code hides the plugin's server.
- **Other agents**: the Codex, Cursor, VS Code, Copilot and Gemini plugins
  always point at `https://api.baserow.io/mcp`, so they can't be tested
  against a local stack. Add the server as above and install only the skill:
  ```bash
  npx skills add baserow/baserow-mcp
  ```

### Endpoint key

On the **Endpoint** tab, create an endpoint. The UI shows the SSE URL with the
key pre-filled:

```
http://localhost:8000/mcp/YOUR_ENDPOINT_KEY/sse
```

- **MCP Inspector**: choose the SSE transport and paste the URL.
- **Claude Desktop, Cursor, Windsurf**: paste the JSON config snippet shown in
  the Baserow UI into the client's config file and restart the client.

The key also works on the OAuth URL as a bearer token:
`Authorization: Bearer YOUR_ENDPOINT_KEY` on `POST http://localhost:8000/mcp`.

## 2. Verify connection

After connecting, your client should list the available Baserow tools. In
Claude Desktop this appears as a hammer icon in the input bar. In MCP
Inspector, tools appear in the left panel after connecting.

## 3. Available tools

The following tools are currently enabled:

| Tool | Description |
|---|---|
| `list_databases` | List all databases in the workspace |
| `list_tables` | List tables, optionally filtered by database |
| `get_table_schema` | Get field names and types for one or more tables |
| `list_table_rows` | List rows with optional search and pagination |
| `create_rows` | Create one or more rows in a table |
| `update_rows` | Update existing rows by ID |
| `delete_rows` | Delete rows by ID |

## 4. Test scenarios

### List databases and tables

Ask Claude: *"What databases do I have in Baserow?"*

Expected: Claude calls `list_databases`, then `list_tables`, and returns the
names and IDs.

### Read table schema

Ask Claude: *"What fields does the [table name] table have?"*

Expected: Claude calls `list_tables` to find the ID, then `get_table_schema`,
and describes the fields.

### Create rows

Ask Claude: *"Add a row to [table name] with Name set to 'Test' and Status set
to 'Active'"*

Expected: Claude calls `get_table_schema` to learn the field names, then
`create_rows` with the correct payload.

### Update rows

Ask Claude: *"Change the Status of row 1 in [table name] to 'Done'"*

Expected: Claude calls `update_rows` with the row ID and new field value.

### Delete rows

Ask Claude: *"Delete row 1 from [table name]"*

Expected: Claude calls `delete_rows` and confirms deletion.

### Search

Ask Claude: *"Find rows in [table name] that contain 'test'"*

Expected: Claude calls `list_table_rows` with a `search` parameter.

## 5. Verify disabled tools are not exposed

The following tools exist in the codebase but are **not** exposed to MCP
clients, whatever is ticked on the consent page:

- `create_database`
- `create_table`, `update_table`, `delete_table`
- `create_fields`, `update_fields`, `delete_fields`

Verify these do **not** appear in your client's tool list.

## 6. Verify tool selection (OAuth)

Connect with OAuth and leave only `list_databases` and `list_tables` ticked on
the consent page. Verify the client lists only those two tools, and that asking
it to create a row fails.

## 7. Verify disconnect

Click **Disconnect** next to the app under **Connected apps**. Verify the next
tool call from the client fails and the client asks you to sign in again.

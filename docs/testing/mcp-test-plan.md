# MCP Manual Test Plan

## Prerequisites

- A running Baserow instance (local dev or deployed)
- For OAuth: `BASEROW_MCP_OAUTH_ENABLED=true` on the backend
- An MCP-compatible client (see step 1)

## 1. Connect an MCP client

Clients connect with OAuth or with an endpoint key. Both are set up under
**My settings > MCP server**.

The steps below use `<server url>`, the backend URL followed by `/mcp`:

- local dev: `http://localhost:8000/mcp`
- baserow.io: `https://api.baserow.io/mcp`
- self-hosted: `<PUBLIC_BACKEND_URL>/mcp`

### OAuth (recommended)

The **OAuth** tab shows `<server url>`. Connect one of these clients:

- **Claude Code**:
  ```bash
  claude mcp add --transport http baserow <server url>
  ```
  Run `/mcp` in Claude Code to sign in.
- **MCP Inspector**: run `npx @modelcontextprotocol/inspector`, choose the
  Streamable HTTP transport and paste `<server url>`.

The [baserow-mcp README](https://github.com/baserow/baserow-mcp#install-per-agent)
has the steps for every other client, including Claude Desktop, claude.ai,
ChatGPT, Codex, Cursor, VS Code and Gemini CLI.

The client opens the Baserow consent page. Pick a workspace and tick the
tools to allow. Only the read tools are ticked on a first connection, so also
tick **Create rows**, **Update rows** and **Delete rows** for the scenarios in
step 4. Approve, and the app shows under **Connected apps** on the OAuth tab.

#### Hosted apps on a local stack

Claude Desktop, claude.ai and ChatGPT connect to Baserow from the internet,
so they can't reach `localhost`. Expose the backend with a tunnel, for example
`cloudflared tunnel --url http://localhost:8000`, set `PUBLIC_BACKEND_URL` to
the tunnel URL and restart the backend. Unset `BASEROW_PUBLIC_URL` if it is
set: it overrides `PUBLIC_BACKEND_URL`, and setting it to the tunnel URL would
also move the frontend there. `<server url>` is then
`<tunnel url>/mcp`.

The server only accepts tokens issued for its current `PUBLIC_BACKEND_URL`.
After the switch, clients set up with `http://localhost:8000/mcp` stop working,
so point every client at the tunnel URL. When you switch back, sign in again
from each client.

### Plugin and skill

[baserow/baserow-mcp](https://github.com/baserow/baserow-mcp) packages the
server config with the `baserow-basics` skill, which teaches the agent how to
use the tools. Test it once on a release candidate:

- **Claude Code**: the plugin asks for the server URL:
  ```
  /plugin marketplace add baserow/baserow-mcp
  /plugin install baserow@baserow
  ```
  Enter `<server url>` when asked (change it later with
  `/plugin configure baserow@baserow`), then run `/mcp`, pick
  `plugin:baserow:baserow` and sign in. Remove any `baserow` server you added
  by hand first, or Claude Code hides the plugin's server.
- **Other agents**: the Codex, Cursor, VS Code, Copilot and Gemini plugins
  always point at `https://api.baserow.io/mcp`. To test another instance, add
  the server by hand as the README describes and install only the skill:
  ```bash
  npx skills add baserow/baserow-mcp
  ```

### Endpoint key

Create an endpoint. With OAuth on, this is on the **Endpoint** tab; with OAuth
off there are no tabs and the page lists the endpoints directly. The UI shows
the SSE URL with the key pre-filled:

```
<backend url>/mcp/YOUR_ENDPOINT_KEY/sse
```

- **MCP Inspector**: choose the SSE transport and paste the URL.
- **Claude Desktop, Cursor, Windsurf**: paste the JSON config snippet shown in
  the Baserow UI into the client's config file and restart the client.

The key also works as a bearer token on `<server url>`. This lists the tools:

```bash
curl -X POST <server url> \
  -H "Authorization: Bearer YOUR_ENDPOINT_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

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
clients. They are not listed on the consent page either:

- `update_table`, `delete_table`

Verify these do **not** appear in your client's tool list.

## 6. Verify tool selection (OAuth)

The consent page only shows again for a new grant, so first disconnect the
app as in step 7. Sign in again from the client and leave only
**List databases** and **List tables** ticked. Verify the client lists only
`list_databases` and `list_tables`, and that asking it to create a row fails.

## 7. Verify disconnect

Click **Disconnect** next to the app under **Connected apps**, then click it
again to confirm. Verify the next tool call from the client fails and the
client asks you to sign in again.

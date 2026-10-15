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

- **Claude Code**:
  ```bash
  claude mcp add --transport http baserow http://localhost:8000/mcp
  ```
  Run `/mcp` in Claude Code to sign in.
- **claude.ai or Claude Desktop**: open **Settings > Connectors**, click
  **Add custom connector** and paste the URL. A local URL only works from
  Claude Desktop; claude.ai needs a public one.
- **MCP Inspector**: run `npx @modelcontextprotocol/inspector`, choose the
  Streamable HTTP transport and paste the URL.

The client opens the Baserow consent page. Pick a workspace and the tools to
allow, then approve. The app then shows under **Connected apps** on the OAuth
tab.

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
